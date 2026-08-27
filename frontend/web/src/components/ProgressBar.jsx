function ProgressBar({ value = 0, className = "" }) {
  const percent = Math.min(100, Math.max(0, value * 100));

  return (
    <div className={`progress-bar ${className}`}>
      <div className="progress-bar__fill" style={{ width: `${percent}%` }} />
    </div>
  );
}

export default ProgressBar;
