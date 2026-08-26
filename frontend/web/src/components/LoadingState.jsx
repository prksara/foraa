function LoadingState({ lines = 3 }) {
  return (
    <div className="loading-state">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="loading-shimmer"
          style={{ width: `${85 - i * 15}%` }}
        />
      ))}
    </div>
  );
}

export default LoadingState;
