function Card({
  children,
  padding = "md",
  hover = false,
  className = "",
  ...props
}) {
  const classes = [
    "card",
    `card--${padding}`,
    hover ? "card--hover" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
}

export default Card;
