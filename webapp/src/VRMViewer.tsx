import { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { VRMLoaderPlugin, VRMUtils } from "@pixiv/three-vrm";

export function VRMViewer({ size = 280, persona = "miko" }: { size?: number; persona?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f1419);

    const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 20);
    camera.position.set(0, 1.1, 2.5);

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true });
    renderer.setSize(size, size);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    const light = new THREE.DirectionalLight(0xffffff, 1.2);
    light.position.set(1, 2, 3);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0xffffff, 0.4));

    const gltfLoader = new GLTFLoader();
    gltfLoader.register((parser) => new VRMLoaderPlugin(parser));

    const url = `/api/avatar.vrm?persona=${encodeURIComponent(persona)}`;

    gltfLoader.load(
      url,
      (gltf) => {
        const vrm = gltf.userData.vrm;
        if (!vrm) return;
        VRMUtils.rotateVRM0(vrm);
        scene.add(vrm.scene);
        vrm.scene.position.y = -0.2;

        // Breathing + slow spin
        const clock = new THREE.Clock();
        const animate = () => {
          requestAnimationFrame(animate);
          const delta = clock.getDelta();
          vrm.scene.rotation.y += delta * 0.3;
          if (vrm.humanoid) {
            vrm.update(delta);
          }
          renderer.render(scene, camera);
        };
        animate();
      },
      undefined,
      (err) => console.error("VRM load error:", err),
    );

    return () => renderer.dispose();
  }, [size, persona]);

  return (
    <canvas
      ref={canvasRef}
      width={size}
      height={size}
      style={{ width: size, height: size, borderRadius: "12px" }}
    />
  );
}
