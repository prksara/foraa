function HealthMetric({ icon, name, value, unit }) {
  const isEmpty = value == null;

  return (
    <div className={`health-metric${isEmpty ? " health-metric--empty" : ""}`}>
      {icon && <div className="health-metric__icon">{icon}</div>}
      <span className="health-metric__name">{name}</span>
      <strong className="health-metric__value">
        {isEmpty ? (
          "—"
        ) : (
          <>
            {value}
            {unit && <small> {unit}</small>}
          </>
        )}
      </strong>
    </div>
  );
}

export default HealthMetric;
