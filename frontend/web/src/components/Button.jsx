function Button({
  children,
  variant = "primary",
  size = "md",
  icon,
  onClick,
  disabled,
  className = "",
  type = "button",
  ...props
}) {
  const classes = [
    "btn",
    `btn--${variant}`,
    size !== "md" ? `btn--${size}` : "",
    icon && !children ? "btn--icon-only" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      className={classes}
      onClick={onClick}
      disabled={disabled}
      type={type}
      {...props}
    >
      {icon && <span className="btn__icon">{icon}</span>}
      {children}
    </button>
  );
}

export default Button;
