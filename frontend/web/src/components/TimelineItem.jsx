function TimelineItem({ date, title, description, icon }) {
  return (
    <div className="timeline-item">
      <div className="timeline-item__marker">
        {icon || <span className="timeline-item__dot" />}
      </div>
      <div className="timeline-item__content">
        <span className="timeline-item__date">{date}</span>
        <strong className="timeline-item__title">{title}</strong>
        {description && (
          <p className="timeline-item__desc">{description}</p>
        )}
      </div>
    </div>
  );
}

export default TimelineItem;
