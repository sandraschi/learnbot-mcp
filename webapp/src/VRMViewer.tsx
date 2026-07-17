import { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { VRMLoaderPlugin, VRMUtils } from "@pixiv/three-vrm";

// VRM 1.0 preset expression names (three-vrm maps VRM0 blendshapes onto these).
// setValue on a missing preset is a safe no-op.
export const VRM_EXPRESSIONS = ["neutral", "happy", "angry", "sad", "relaxed", "surprised"] as const;
export type VrmExpression = (typeof VRM_EXPRESSIONS)[number];

const VISEMES = ["aa", "ih", "ou", "ee", "oh"] as const;

interface VRMViewerProps {
  size?: number;
  persona?: string;
  /** Active facial expression (smoothly blended). */
  expression?: VrmExpression;
  /** Cycle mouth visemes - lip-sync placeholder / talking test. */
  talking?: boolean;
  /** Eyes follow the mouse cursor. */
  lookAtMouse?: boolean;
  /** Slow turntable spin (drag always overrides while held). */
  autoRotate?: boolean;
}

export function VRMViewer({
  size = 280,
  persona = "miko",
  expression = "neutral",
  talking = false,
  lookAtMouse = true,
  autoRotate = true,
}: VRMViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Control values live in refs so the render loop sees changes without
  // tearing down the scene (scene rebuild only on size/persona change).
  const expressionRef = useRef<VrmExpression>(expression);
  const talkingRef = useRef(talking);
  const lookAtRef = useRef(lookAtMouse);
  const autoRotateRef = useRef(autoRotate);

  useEffect(() => {
    expressionRef.current = expression;
    talkingRef.current = talking;
    lookAtRef.current = lookAtMouse;
    autoRotateRef.current = autoRotate;
  }, [expression, talking, lookAtMouse, autoRotate]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f1419);

    const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 20);
    camera.position.set(0, 1.1, 2.5);
    scene.add(camera); // so camera-attached lookAt target is in the graph

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true });
    renderer.setSize(size, size);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Interactivity: drag to orbit, wheel to zoom.
    const controls = new OrbitControls(camera, canvas);
    controls.target.set(0, 0.95, 0);
    controls.enablePan = false;
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 0.6;
    controls.maxDistance = 6;
    controls.autoRotateSpeed = 2.0;

    const light = new THREE.DirectionalLight(0xffffff, 1.2);
    light.position.set(1, 2, 3);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0xffffff, 0.4));

    // Eyes-follow-cursor target, positioned in camera space from mouse NDC.
    const lookAtTarget = new THREE.Object3D();
    camera.add(lookAtTarget);
    lookAtTarget.position.set(0, 0, -2);
    const onMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const ny = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      lookAtTarget.position.set(nx * 0.9, ny * 0.6, -2);
    };
    canvas.addEventListener("mousemove", onMouseMove);

    const gltfLoader = new GLTFLoader();
    gltfLoader.register((parser) => new VRMLoaderPlugin(parser));

    const url = `/api/avatar.vrm?persona=${encodeURIComponent(persona)}`;

    let rafId = 0;
    let disposed = false;

    gltfLoader.load(
      url,
      (gltf) => {
        if (disposed) return;
        const vrm = gltf.userData.vrm;
        if (!vrm) return;
        VRMUtils.rotateVRM0(vrm);
        scene.add(vrm.scene);
        vrm.scene.position.y = -0.2;

        if (vrm.lookAt) vrm.lookAt.target = lookAtTarget;

        // Natural rest pose: VRM models load in T-pose (arms straight out).
        // Normalized humanoid rig: identity = T-pose, left arm along +X,
        // right along -X, world Z toward viewer. Rotating about Z drops the
        // arms: left needs negative z, right positive. ~69 degrees down plus
        // a relaxed elbow. (If a model ever salutes the sky, flip the signs.)
        const ARM_DOWN = 1.2;
        const bones = {
          leftUpper: vrm.humanoid?.getNormalizedBoneNode("leftUpperArm") ?? null,
          rightUpper: vrm.humanoid?.getNormalizedBoneNode("rightUpperArm") ?? null,
          leftLower: vrm.humanoid?.getNormalizedBoneNode("leftLowerArm") ?? null,
          rightLower: vrm.humanoid?.getNormalizedBoneNode("rightLowerArm") ?? null,
          spine: vrm.humanoid?.getNormalizedBoneNode("spine") ?? null,
        };

        // Expression blending state
        const current: Record<string, number> = {};
        // Auto-blink state
        let nextBlink = 1.5;
        let blinkPhase = -1; // -1 = idle, else 0..1 progress
        // Viseme state
        let visemeTimer = 0;
        let activeViseme: string | null = null;

        const clock = new THREE.Clock();

        const animate = () => {
          if (disposed) return;
          rafId = requestAnimationFrame(animate);
          const delta = clock.getDelta();
          const t = clock.elapsedTime;

          controls.autoRotate = autoRotateRef.current;
          controls.update();

          const em = vrm.expressionManager;
          if (em) {
            // Smoothly blend toward the selected expression
            for (const name of VRM_EXPRESSIONS) {
              const target = name === expressionRef.current && name !== "neutral" ? 1 : 0;
              current[name] = (current[name] ?? 0) + ((target - (current[name] ?? 0)) * Math.min(1, delta * 8));
              em.setValue(name, current[name]);
            }

            // Auto-blink (skip mid-blink retrigger)
            if (blinkPhase < 0 && t > nextBlink) blinkPhase = 0;
            if (blinkPhase >= 0) {
              blinkPhase += delta / 0.18; // blink duration ~180ms
              const w = blinkPhase < 0.5 ? blinkPhase * 2 : Math.max(0, 2 - blinkPhase * 2);
              em.setValue("blink", Math.min(1, w));
              if (blinkPhase >= 1) {
                blinkPhase = -1;
                nextBlink = t + 2 + Math.random() * 4;
                em.setValue("blink", 0);
              }
            }

            // Talking: cycle visemes; decay when quiet
            if (talkingRef.current) {
              visemeTimer -= delta;
              if (visemeTimer <= 0) {
                if (activeViseme) em.setValue(activeViseme, 0);
                activeViseme = VISEMES[Math.floor(Math.random() * VISEMES.length)];
                em.setValue(activeViseme, 0.35 + Math.random() * 0.55);
                visemeTimer = 0.09 + Math.random() * 0.12;
              }
            } else if (activeViseme) {
              em.setValue(activeViseme, 0);
              activeViseme = null;
            }
          }

          // Idle pose: arms down with a barely-visible breathing sway
          const sway = Math.sin(t * 1.4) * 0.015;
          if (bones.leftUpper) bones.leftUpper.rotation.z = -(ARM_DOWN + sway);
          if (bones.rightUpper) bones.rightUpper.rotation.z = ARM_DOWN + sway;
          if (bones.leftLower) bones.leftLower.rotation.z = -0.15;
          if (bones.rightLower) bones.rightLower.rotation.z = 0.15;
          if (bones.spine) bones.spine.rotation.x = Math.sin(t * 1.1) * 0.012;

          // Eyes: detach target when look-at is off
          if (vrm.lookAt) vrm.lookAt.target = lookAtRef.current ? lookAtTarget : null;

          vrm.update(delta);
          renderer.render(scene, camera);
        };
        animate();
      },
      undefined,
      (err) => console.warn("VRM load error:", err),
    );

    return () => {
      disposed = true;
      cancelAnimationFrame(rafId);
      canvas.removeEventListener("mousemove", onMouseMove);
      controls.dispose();
      renderer.dispose();
    };
  }, [size, persona]);

  return (
    <canvas
      ref={canvasRef}
      width={size}
      height={size}
      style={{ width: size, height: size, borderRadius: "12px", cursor: "grab", touchAction: "none" }}
    />
  );
}
