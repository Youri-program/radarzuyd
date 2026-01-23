import type { Detection } from "../types";

interface DetectionListProps {
  detections: Detection[];
}

export const DetectionList: React.FC<DetectionListProps> = ({ detections }) => {
  if (!detections.length) {
    return (
      <div className="text-sm text-slate-400">
        No detections available. Once the model is integrated, detected objects
        will be listed here.
      </div>
    );
  }

  return (
    <table className="w-full text-sm">
      <thead className="text-xs uppercase text-slate-400 border-b border-slate-800">
        <tr>
          <th className="text-left py-1 font-medium">Label</th>
          <th className="text-left py-1 font-medium">Confidence</th>
        </tr>
      </thead>
      <tbody>
        {detections.map((d, index) => (
          <tr
            key={index}
            className="border-b border-slate-900/60 hover:bg-slate-900/40 transition-colors"
          >
            <td className="py-1.5 text-slate-100">{d.label}</td>
            <td className="py-1.5 font-mono text-emerald-400">
              {(d.confidence * 100).toFixed(1)}%
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
