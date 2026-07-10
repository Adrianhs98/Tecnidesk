import { useState } from "react";

export default function LogoBadge({ businessName = "TecniDesk", subtitle = "Portal de Rastreo", logoUrl = null }) {
  const [imgError, setImgError] = useState(false);

  return (
    <div className="logo-badge" style={{ overflow: "hidden" }}>
      {!imgError ? (
        <img
          src={logoUrl || "/logo.png"}
          alt={`Logo de ${businessName}`}
          onError={() => setImgError(true)}
          style={{ width: 20, height: 20, objectFit: "contain", borderRadius: 4 }}
        />
      ) : (
        <span style={{ width: 20, height: 20, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: "var(--accent)", background: "rgba(201,167,106,0.12)", borderRadius: 4 }}>
          {businessName.charAt(0).toUpperCase()}
        </span>
      )}
      <div className="logo-dot" />
      <span className="logo-text" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {businessName} | {subtitle}
      </span>
    </div>
  );
}
