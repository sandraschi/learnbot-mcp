import { useEffect, useState } from "react";
import { ShieldCheck, FileText, UserCheck, Clock } from "lucide-react";
import { api } from "../api";

export function Compliance() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .compliance()
      .then(setData)
      .catch(() => setErr("Failed to load compliance info"));
  }, []);

  if (err) return <div className="text-red-400 text-sm">{err}</div>;
  if (!data)
    return <div className="text-zinc-500 text-sm">Loading...</div>;

  const items = [
    {
      icon: ShieldCheck,
      label: "Regulatory Regime",
      value: data.regime || "none",
    },
    {
      icon: UserCheck,
      label: "Real-Name Auth",
      value: data.real_name_auth ? "Required" : "Not required",
    },
    {
      icon: Clock,
      label: "Conversation Retention",
      value: `${data.retention_days} days`,
    },
    {
      icon: FileText,
      label: "Disclosure",
      value: data.disclosure || "None configured",
    },
  ];

  return (
    <div data-testid="compliance-page">
      <h1 className="text-xl font-bold mb-6">Compliance</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {items.map(({ icon: Icon, label, value }) => (
          <div
            key={label}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"
          >
            <div className="flex items-center gap-3">
              <Icon className="w-5 h-5 text-amber-500 shrink-0" />
              <div>
                <div className="text-sm font-medium">{label}</div>
                <div className="text-sm text-zinc-500">{value}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <h2 className="text-lg font-semibold mb-3">Refusal Templates</h2>
      <div className="space-y-2">
        {Object.entries(data.refusal_templates || {}).map(
          ([topic, message]: [string, any]) => (
            <div
              key={topic}
              className="bg-zinc-900 border border-zinc-800 rounded-xl p-3"
            >
              <div className="text-sm font-medium">{topic}</div>
              <div className="text-sm text-zinc-500">{String(message)}</div>
            </div>
          )
        )}
      </div>
    </div>
  );
}
