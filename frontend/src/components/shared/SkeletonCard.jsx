export default function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton-line" style={{ width: "60%", height: "24px" }} />
      <div className="skeleton-line" style={{ width: "40%", height: "14px" }} />
      <div className="skeleton-line" style={{ width: "100%", height: "60px", marginTop: "8px" }} />
      <div className="skeleton-line" style={{ width: "100%", height: "40px" }} />
      <div style={{ display: "flex", gap: "12px" }}>
        <div className="skeleton-line" style={{ flex: 1, height: "80px" }} />
        <div className="skeleton-line" style={{ flex: 1, height: "80px" }} />
      </div>
    </div>
  );
}
