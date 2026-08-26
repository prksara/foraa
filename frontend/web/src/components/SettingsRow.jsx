function SettingsRow({ label, description, children }) {
  return (
    <div className="settings-row">
      <div className="settings-row__info">
        <span className="settings-row__label">{label}</span>
        {description && (
          <span className="settings-row__desc">{description}</span>
        )}
      </div>
      <div className="settings-row__control">{children}</div>
    </div>
  );
}

export default SettingsRow;
