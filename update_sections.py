import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the About section to map FOCUS to data if possible, or remove invented content
# Wait, user asked to remove "FOCUS" and "APPROACH" if invented. I will just use summary.
old_about = re.search(r'<div class="editorial-about-grid reveal-up">.*?</div>\n        </div>', content, re.DOTALL)
if old_about:
    new_about = '''<div class="editorial-about-grid reveal-up">
          <div class="about-meta-col">
            <span class="designer-section-tag">// 01</span>
          </div>
          <div class="about-text-col">
            <p class="about-editorial-text">{escape(summary)}</p>
          </div>
        </div>'''
    content = content.replace(old_about.group(0), new_about)


# Skills replacement
old_skills = re.search(r'def build_designer_skills_section.*?return f"""(?:(?!</section>""").)*</section>"""', content, re.DOTALL).group(0)
new_skills = '''def build_designer_skills_section(skills: list) -> str:
    if not skills:
        return ""
    import html
    items = [f'<span class="skill-editorial-item">{html.escape(str(s).strip()).upper()}</span>' for s in skills if s and str(s).strip()]
    if not items: return ""
    skills_html = ' <span class="skill-separator">&#8212;</span> '.join(items)
    return f"""
    <!-- Designer Skills Section (02 // ARSENAL) -->
    <section id="skills" class="designer-section">
      <div class="designer-container">
        <div class="section-header-designer reveal-left">
          <div class="header-tag-group">
            <span class="designer-section-tag">// 02</span>
            <h2 class="designer-section-title">Technical Mastery</h2>
          </div>
        </div>
        <div class="editorial-skills-list reveal-up">
          {skills_html}
        </div>
      </div>
    </section>\"\"\"'''
content = content.replace(old_skills, new_skills)

# Projects replacement
old_projects = re.search(r'def build_designer_projects_section.*?return f"""(?:(?!</section>""").)*</section>"""', content, re.DOTALL).group(0)
new_projects = '''def build_designer_projects_section(projects: list) -> str:
    if not projects: return ""
    cards = []
    import html
    for idx, proj in enumerate(projects):
        if not isinstance(proj, dict): continue
        title = proj.get("title", "").strip()
        if not title: continue
        desc = proj.get("description", "").strip()
        techs = proj.get("technologies") or []
        link = proj.get("link", "").strip()
        num_str = f"{idx + 1:02d}"
        tech_tags = [f'<span class="editorial-tech-tag">{html.escape(t.strip()).upper()}</span>' for t in techs]
        tech_tags_html = '\\n                '.join(tech_tags)
        link_html = ""
        if link:
            href = html.escape(link if link.startswith("http") else f"https://{link}")
            link_html = f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="editorial-project-btn">VIEW PROJECT &rarr;</a>'
        cards.append(f"""
        <div class="editorial-project-row reveal-up">
          <div class="project-num-col"><span class="project-num">{num_str}</span></div>
          <div class="project-content-col">
            <h3 class="project-huge-title">{html.escape(title)}</h3>
            <div class="project-techs">{tech_tags_html}</div>
            <p class="project-editorial-desc">{html.escape(desc)}</p>
            <div class="project-action">{link_html}</div>
          </div>
        </div>""")
    if not cards: return ""
    cards_html = '\\n'.join(cards)
    return f"""
    <!-- Designer Projects Section -->
    <section id="projects" class="designer-section">
      <div class="designer-container">
        <div class="section-header-designer reveal-left">
          <div class="header-tag-group">
            <span class="designer-section-tag">// 03</span>
            <h2 class="designer-section-title">Selected Projects</h2>
          </div>
        </div>
        <div class="editorial-projects-list">
          {cards_html}
        </div>
      </div>
    </section>\"\"\"'''
content = content.replace(old_projects, new_projects)

# Experience replacement
old_exp = re.search(r'def build_designer_experience_section.*?return f"""(?:(?!</section>""").)*</section>"""', content, re.DOTALL).group(0)
new_exp = '''def build_designer_experience_section(experience: list) -> str:
    if not experience: return ""
    items = []
    import html
    for idx, exp in enumerate(experience):
        if not isinstance(exp, dict): continue
        role = exp.get("role", "").strip()
        company = exp.get("company", "").strip()
        dates = exp.get("dates", "").strip()
        resp = exp.get("responsibilities") or []
        resp_items = [f'<li>{html.escape(r)}</li>' for r in resp if r and str(r).strip()]
        resp_html = f'<ul class="editorial-resp-list">\\n              ' + '\\n              '.join(resp_items) + '\\n            </ul>' if resp_items else ""
        items.append(f"""
        <div class="editorial-timeline-row reveal-up">
          <div class="timeline-date-col">{html.escape(dates)}</div>
          <div class="timeline-info-col">
            <h3 class="timeline-role">{html.escape(role)}</h3>
            <div class="timeline-company">{html.escape(company)}</div>
            {resp_html}
          </div>
        </div>""")
    if not items: return ""
    items_html = '\\n'.join(items)
    return f"""
    <!-- Designer Experience Section -->
    <section id="experience" class="designer-section">
      <div class="designer-container">
        <div class="section-header-designer reveal-left">
          <div class="header-tag-group">
            <span class="designer-section-tag">// 04</span>
            <h2 class="designer-section-title">Experience</h2>
          </div>
        </div>
        <div class="editorial-timeline-list">
          {items_html}
        </div>
      </div>
    </section>\"\"\"'''
content = content.replace(old_exp, new_exp)

# Education replacement
old_edu = re.search(r'def build_designer_education_section.*?return f"""(?:(?!</section>""").)*</section>"""', content, re.DOTALL).group(0)
new_edu = '''def build_designer_education_section(education: list) -> str:
    if not education: return ""
    items = []
    import html
    for idx, edu in enumerate(education):
        if not isinstance(edu, dict): continue
        degree = edu.get("degree", "").strip()
        inst = edu.get("institution", "").strip()
        dates = edu.get("dates", "").strip()
        details = edu.get("details", "").strip()
        details_html = f'<p class="timeline-details">{html.escape(details)}</p>' if details else ""
        items.append(f"""
        <div class="editorial-timeline-row reveal-up">
          <div class="timeline-date-col">{html.escape(dates)}</div>
          <div class="timeline-info-col">
            <h3 class="timeline-role">{html.escape(degree)}</h3>
            <div class="timeline-company">{html.escape(inst)}</div>
            {details_html}
          </div>
        </div>""")
    if not items: return ""
    items_html = '\\n'.join(items)
    return f"""
    <!-- Designer Education Section -->
    <section id="education" class="designer-section">
      <div class="designer-container">
        <div class="section-header-designer reveal-left">
          <div class="header-tag-group">
            <span class="designer-section-tag">// 05</span>
            <h2 class="designer-section-title">Education</h2>
          </div>
        </div>
        <div class="editorial-timeline-list">
          {items_html}
        </div>
      </div>
    </section>\"\"\"'''
content = content.replace(old_edu, new_edu)

# Achievements replacement
old_ach = re.search(r'def build_designer_achievements_section.*?return f"""(?:(?!</section>""").)*</section>"""', content, re.DOTALL).group(0)
new_ach = '''def build_designer_achievements_section(achievements: list) -> str:
    if not achievements: return ""
    cards = []
    import html
    for idx, ach in enumerate(achievements):
        if isinstance(ach, str) and ach.strip():
            cards.append(f"""
            <div class="editorial-achieve-row reveal-up">
              <div class="achieve-bullet">&#x2736;</div>
              <p class="achieve-statement">{html.escape(ach.strip())}</p>
            </div>""")
    if not cards: return ""
    cards_html = '\\n'.join(cards)
    return f"""
    <!-- Designer Achievements Section -->
    <section id="achievements" class="designer-section">
      <div class="designer-container">
        <div class="section-header-designer reveal-left">
          <div class="header-tag-group">
            <span class="designer-section-tag">// 06</span>
            <h2 class="designer-section-title">Achievements</h2>
          </div>
        </div>
        <div class="editorial-achieve-list">
          {cards_html}
        </div>
      </div>
    </section>\"\"\"'''
content = content.replace(old_ach, new_ach)

# Contact replacement
old_cont = re.search(r'def build_designer_contact_section.*?return f"""(?:(?!</section>""").)*</section>"""', content, re.DOTALL).group(0)
new_cont = '''def build_designer_contact_section(contact: dict) -> str:
    email = contact.get("email", "").strip()
    phone = contact.get("phone", "").strip()
    linkedin = contact.get("linkedin", "").strip()
    github = contact.get("github", "").strip()
    project_links = contact.get("project_links") or []
    if not any([email, phone, linkedin, github, project_links]): return ""
    buttons = []
    import html
    if email: buttons.append(f'<a href="mailto:{html.escape(email)}" class="editorial-contact-link reveal-up">EMAIL</a>')
    if linkedin:
        href = html.escape(linkedin if linkedin.startswith("http") else f"https://{linkedin}")
        buttons.append(f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="editorial-contact-link reveal-up">LINKEDIN</a>')
    if github:
        href = html.escape(github if github.startswith("http") else f"https://{github}")
        buttons.append(f'<a href="{href}" target="_blank" rel="noopener noreferrer" class="editorial-contact-link reveal-up">GITHUB</a>')
    buttons_html = '\\n            '.join(buttons)
    return f"""
    <!-- Designer Contact Section -->
    <section id="contact" class="designer-section">
      <div class="designer-container">
        <div class="editorial-contact-box">
          <h2 class="contact-huge-title reveal-up">LET&apos;S TALK</h2>
          <div class="editorial-contact-grid">
            {buttons_html}
          </div>
        </div>
      </div>
    </section>\"\"\"'''
content = content.replace(old_cont, new_cont)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Now append CSS to style-designer.css
css_append = '''
/* --------------------------------------------------------------------------
   SECTIONS 3-9: EDITORIAL ADDITIONS
   -------------------------------------------------------------------------- */

/* Section Headers Override */
.section-header-designer {
  border-top: 1px solid var(--d-border);
  padding-top: 16px;
  margin-bottom: 60px;
  display: flex;
  justify-content: space-between;
}
.header-tag-group {
  display: flex;
  align-items: center;
  gap: 16px;
}
.designer-section-tag {
  font-family: var(--d-font-mono);
  color: var(--d-accent);
  font-size: 0.8rem;
}
.designer-section-title {
  font-family: var(--d-font-body);
  font-size: 1.4rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Skills */
.editorial-skills-list {
  font-family: var(--d-font-body);
  font-size: clamp(2rem, 4vw, 3.5rem);
  font-weight: 700;
  line-height: 1.4;
  color: var(--d-text-primary);
  text-transform: uppercase;
  max-width: 1000px;
}
.skill-separator {
  color: var(--d-accent);
  margin: 0 12px;
  opacity: 0.5;
}

/* Projects */
.editorial-project-row {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 40px;
  border-top: 1px solid var(--d-border);
  padding-top: 40px;
  padding-bottom: 80px;
}
.project-num {
  font-family: var(--d-font-mono);
  color: var(--d-text-secondary);
  font-size: 1rem;
}
.project-huge-title {
  font-family: var(--d-font-editorial);
  font-size: clamp(3rem, 6vw, 5rem);
  line-height: 1;
  margin-bottom: 24px;
}
.project-techs {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}
.editorial-tech-tag {
  font-family: var(--d-font-mono);
  font-size: 0.75rem;
  padding: 4px 10px;
  border: 1px solid var(--d-border);
  border-radius: 4px;
  color: var(--d-accent);
}
.project-editorial-desc {
  font-size: 1.1rem;
  color: var(--d-text-secondary);
  line-height: 1.6;
  max-width: 600px;
  margin-bottom: 32px;
}
.editorial-project-btn {
  font-family: var(--d-font-mono);
  color: var(--d-text-primary);
  text-decoration: none;
  font-size: 0.85rem;
  letter-spacing: 0.1em;
  border-bottom: 1px solid var(--d-accent);
  padding-bottom: 4px;
  transition: color 0.3s;
}
.editorial-project-btn:hover {
  color: var(--d-accent);
}

/* Timeline (Experience / Education) */
.editorial-timeline-row {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 40px;
  border-top: 1px solid var(--d-border);
  padding-top: 32px;
  padding-bottom: 48px;
}
.timeline-date-col {
  font-family: var(--d-font-mono);
  color: var(--d-text-secondary);
  font-size: 0.9rem;
}
.timeline-role {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: 8px;
}
.timeline-company {
  color: var(--d-accent);
  font-family: var(--d-font-mono);
  font-size: 0.9rem;
  margin-bottom: 24px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.editorial-resp-list {
  list-style: none;
  color: var(--d-text-secondary);
  font-size: 1rem;
  line-height: 1.6;
}
.editorial-resp-list li {
  position: relative;
  padding-left: 20px;
  margin-bottom: 12px;
}
.editorial-resp-list li::before {
  content: "—";
  position: absolute;
  left: 0;
  color: var(--d-accent);
}
.timeline-details {
  color: var(--d-text-secondary);
  line-height: 1.6;
}

/* Achievements */
.editorial-achieve-row {
  display: flex;
  gap: 24px;
  border-top: 1px solid var(--d-border);
  padding-top: 24px;
  padding-bottom: 24px;
  align-items: center;
}
.achieve-bullet {
  color: var(--d-accent);
  font-size: 1.5rem;
}
.achieve-statement {
  font-size: 1.2rem;
  color: var(--d-text-primary);
}

/* Contact */
.editorial-contact-box {
  padding: 80px 0;
  text-align: center;
}
.editorial-contact-box .contact-huge-title {
  font-family: var(--d-font-editorial);
  font-size: clamp(4rem, 10vw, 8rem);
  line-height: 1;
  margin-bottom: 48px;
}
.editorial-contact-grid {
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
}
.editorial-contact-link {
  font-family: var(--d-font-mono);
  font-size: 1.2rem;
  color: var(--d-text-primary);
  text-decoration: none;
  border-bottom: 2px solid var(--d-accent);
  padding-bottom: 4px;
  transition: color 0.3s;
}
.editorial-contact-link:hover {
  color: var(--d-accent);
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .editorial-about-grid, .hero-statement-grid {
    grid-template-columns: 1fr;
    gap: 32px;
  }
  .editorial-project-row, .editorial-timeline-row {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}
'''
with open('style-designer.css', 'a', encoding='utf-8') as f:
    f.write(css_append)
