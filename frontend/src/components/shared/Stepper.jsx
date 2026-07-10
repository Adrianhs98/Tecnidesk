import { STATUS_CONFIG, STEPS } from "../../utils/constants";

export default function Stepper({ status }) {
  const currentStep = STATUS_CONFIG[status]?.step ?? 0;

  if (status === "NO_APROBADO") {
    return (
      <div className="stepper-section">
        <div style={{ textAlign: "center", padding: "8px 0", color: "#C4837A", fontSize: "14px", fontWeight: 500 }}>
          Esta orden no fue aprobada para reparacion.
        </div>
      </div>
    );
  }

  return (
    <div className="stepper-section">
      <div className="stepper">
        {STEPS.map((step, i) => {
          const stepVal = STATUS_CONFIG[step.key]?.step ?? 0;
          const isActive = step.key === status;
          const isDone = stepVal < currentStep || (stepVal === currentStep && !isActive);
          const cls = isActive ? "active" : isDone ? "done" : "";

          return (
            <div key={step.key} style={{ display: "contents" }}>
              <div className="step-item">
                <div className={`step-circle ${cls}`}>{isDone ? "OK" : i + 1}</div>
                <div className={`step-label ${cls}`}>{step.label}</div>
              </div>
              {i < STEPS.length - 1 && <div className={`step-line ${isDone ? "done" : ""}`} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
