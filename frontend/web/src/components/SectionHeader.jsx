function SectionHeader({ eyebrow, title, action }) {
  return (
    <div className="section-hdr">
      <div>
        {eyebrow && (
          <span className="section-hdr__eyebrow">{eyebrow}</span>
        )}
        <h2 className="section-hdr__title">{title}</h2>
      </div>
      {action && (
        <button
          className="section-hdr__action"
          onClick={action.onClick}
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

export default SectionHeader;
