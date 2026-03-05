from app.utils.email.core import _send_email, _get_template
from typing import List

def _base_email(header_gradient: str,header_emoji: str,header_subtitle: str,body_html: str,footer_text: str,) -> str:
    return f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0"
           style="background-color:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#ffffff;border-radius:12px;
                  box-shadow:0 4px 16px rgba(0,0,0,0.08);overflow:hidden;">

      <!-- Header -->
      <tr>
        <td style="background:{header_gradient};padding:40px;text-align:center;">
          <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:700;">Agile App</h1>
          <p style="margin:8px 0 0;color:rgba(255,255,255,0.9);font-size:15px;">
            {header_emoji} {header_subtitle}
          </p>
        </td>
      </tr>

      <!-- Body -->
      <tr><td style="padding:40px;">{body_html}</td></tr>

      <!-- Footer -->
      <tr>
        <td style="background:#f7fafc;padding:24px 40px;
                   border-top:1px solid #e2e8f0;text-align:center;">
          <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
            {footer_text}
          </p>
        </td>
      </tr>

    </table>
    </td></tr>
    </table>
    </body>
    </html>"""

def _info_box(label: str, value: str, bg: str = "#f7fafc", border: str = "#e2e8f0",
              label_color: str = "#a0aec0", value_color: str = "#1a202c") -> str:
    return f"""
    <p style="margin:0 0 4px;font-size:11px;color:{label_color};
              text-transform:uppercase;letter-spacing:1px;font-weight:600;">{label}</p>
    <p style="margin:0 0 16px;color:{value_color};font-size:15px;font-weight:600;">{value}</p>"""

def _card_box(content: str, bg: str = "#f7fafc", border: str = "#e2e8f0") -> str:
    return f"""
    <table width="100%"
           style="background:{bg};border-radius:10px;border:1px solid {border};
                  margin-bottom:24px;">
      <tr><td style="padding:24px;">{content}</td></tr>
    </table>"""

def _stat_pill(label: str, value: str, color: str) -> str:
    return f"""
    <td style="text-align:center;padding:0 12px;">
      <p style="margin:0 0 4px;font-size:24px;font-weight:700;color:{color};">{value}</p>
      <p style="margin:0;font-size:12px;color:#718096;text-transform:uppercase;
                letter-spacing:1px;">{label}</p>
    </td>"""

_ASSIGNED_CONTENT = {
    "en": {
        "subtitle":     "You've been assigned to an issue 📋",
        "greeting":     "Hi",
        "body":         lambda c, p, by: f"<strong>{by}</strong> has assigned you to an issue on the <strong>{p}</strong> Scrum board.",
        "issue_label":  "Issue",
        "project_label":"Project",
        "assigned_label":"Assigned by",
        "footer":       "This is an automated message from Agile App.",
    },
    "hi": {
        "subtitle":     "आपको एक इश्यू सौंपा गया है 📋",
        "greeting":     "नमस्ते",
        "body":         lambda c, p, by: f"<strong>{by}</strong> ने आपको <strong>{p}</strong> Scrum बोर्ड पर एक इश्यू सौंपा है।",
        "issue_label":  "इश्यू",
        "project_label":"प्रोजेक्ट",
        "assigned_label":"द्वारा सौंपा गया",
        "footer":       "यह Agile App का स्वचालित संदेश है।",
    },
    "fr": {
        "subtitle":     "Un problème vous a été assigné 📋",
        "greeting":     "Bonjour",
        "body":         lambda c, p, by: f"<strong>{by}</strong> vous a assigné(e) à un problème sur le tableau Scrum <strong>{p}</strong>.",
        "issue_label":  "Problème",
        "project_label":"Projet",
        "assigned_label":"Assigné(e) par",
        "footer":       "Ceci est un message automatique d'Agile App.",
    },
    "zh": {
        "subtitle":     "您被分配了一个问题 📋",
        "greeting":     "您好",
        "body":         lambda c, p, by: f"<strong>{by}</strong> 在 <strong>{p}</strong> Scrum 看板上将一个问题分配给了您。",
        "issue_label":  "问题",
        "project_label":"项目",
        "assigned_label":"由此人分配",
        "footer":       "这是来自 Agile App 的自动消息。",
    },
}

_ASSIGNED_SUBJECTS = {
    "en": 'You\'ve been assigned to "{issue}" on Agile App',
    "hi": 'Agile App पर "{issue}" आपको सौंपा गया है',
    "fr": 'Le problème "{issue}" vous a été assigné sur Agile App',
    "zh": 'Agile App 上的问题"{issue}"已分配给您',
}

def _build_assigned_html(lang: str, username: str, issue_title: str,project_name: str, assigned_by: str,) -> str:
    c = _ASSIGNED_CONTENT[lang]
    body = f"""
      <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">
        {c['greeting']} <strong>{username}</strong>,
      </p>
      <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
        {c['body'](issue_title, project_name, assigned_by)}
      </p>
      {_card_box(
          _info_box(c['issue_label'],   issue_title,   value_color="#1a202c") +
          _info_box(c['project_label'], project_name,  value_color="#4a5568")
      )}
      <table width="100%" style="background:#ebf8ff;border-radius:8px;border:1px solid #bee3f8;">
        <tr><td style="padding:16px 20px;">
          <p style="margin:0;color:#2b6cb0;font-size:14px;">
            👤 {c['assigned_label']}: <strong>{assigned_by}</strong>
          </p>
        </td></tr>
      </table>"""
    return _base_email(
        header_gradient = "linear-gradient(135deg,#667eea 0%,#764ba2 100%)",
        header_emoji    = "📋",
        header_subtitle = c["subtitle"],
        body_html       = body,
        footer_text     = c["footer"],
    )

_SPRINT_STARTED_CONTENT = {
    "en": {
        "subtitle":      "Your sprint has started 🚀",
        "greeting":      "Hi",
        "body":          lambda sn, count: f"Sprint <strong>{sn}</strong> is now active. You have <strong>{count}</strong> issue(s) assigned to you in this sprint.",
        "issues_label":  "Your Issues",
        "sprint_label":  "Sprint",
        "project_label": "Project",
        "footer":        "This is an automated message from Agile App.",
    },
    "hi": {
        "subtitle":      "आपका स्प्रिंट शुरू हो गया है 🚀",
        "greeting":      "नमस्ते",
        "body":          lambda sn, count: f"स्प्रिंट <strong>{sn}</strong> अब सक्रिय है। इस स्प्रिंट में आपको <strong>{count}</strong> इश्यू सौंपे गए हैं।",
        "issues_label":  "आपके इश्यू",
        "sprint_label":  "स्प्रिंट",
        "project_label": "प्रोजेक्ट",
        "footer":        "यह Agile App का स्वचालित संदेश है।",
    },
    "fr": {
        "subtitle":      "Votre sprint a commencé 🚀",
        "greeting":      "Bonjour",
        "body":          lambda sn, count: f"Le sprint <strong>{sn}</strong> est maintenant actif. Vous avez <strong>{count}</strong> problème(s) qui vous sont assignés dans ce sprint.",
        "issues_label":  "Vos problèmes",
        "sprint_label":  "Sprint",
        "project_label": "Projet",
        "footer":        "Ceci est un message automatique d'Agile App.",
    },
    "zh": {
        "subtitle":      "您的冲刺已开始 🚀",
        "greeting":      "您好",
        "body":          lambda sn, count: f"冲刺 <strong>{sn}</strong> 现已激活。本次冲刺中您共有 <strong>{count}</strong> 个问题待处理。",
        "issues_label":  "您的问题",
        "sprint_label":  "冲刺",
        "project_label": "项目",
        "footer":        "这是来自 Agile App 的自动消息。",
    },
}

_SPRINT_STARTED_SUBJECTS = {
    "en": 'Sprint "{sprint}" has started — {count} issue(s) assigned to you',
    "hi": 'स्प्रिंट "{sprint}" शुरू हो गया — आपको {count} इश्यू सौंपे गए',
    "fr": 'Le sprint "{sprint}" a commencé — {count} problème(s) vous sont assignés',
    "zh": '冲刺"{sprint}"已开始 — 您有{count}个问题待处理',
}

def _build_sprint_started_html(lang: str, username: str, sprint_name: str,project_name: str, assigned_issues: List[str],) -> str:
    c = _SPRINT_STARTED_CONTENT[lang]
    issue_rows = "".join(
        f'<tr><td style="padding:6px 0;border-bottom:1px solid #e2e8f0;'
        f'color:#2d3748;font-size:14px;">• {title}</td></tr>'
        for title in assigned_issues
    )
    issues_table = f"""
      <table width="100%"
             style="background:#f7fafc;border-radius:10px;border:1px solid #e2e8f0;
                    margin-bottom:24px;">
        <tr><td style="padding:16px 24px 8px;">
          <p style="margin:0 0 12px;font-size:11px;color:#a0aec0;text-transform:uppercase;
                    letter-spacing:1px;font-weight:600;">{c['issues_label']}</p>
          <table width="100%">{issue_rows}</table>
        </td></tr>
      </table>"""
    body = f"""
      <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">
        {c['greeting']} <strong>{username}</strong>,
      </p>
      <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
        {c['body'](sprint_name, len(assigned_issues))}
      </p>
      {issues_table}
      {_card_box(_info_box(c['sprint_label'], sprint_name) + _info_box(c['project_label'], project_name))}"""
    return _base_email(
        header_gradient = "linear-gradient(135deg,#667eea 0%,#764ba2 100%)",
        header_emoji    = "🚀",
        header_subtitle = c["subtitle"],
        body_html       = body,
        footer_text     = c["footer"],
    )

_SPRINT_COMPLETED_CONTENT = {
    "en": {
        "subtitle":        "Sprint completed 🏁",
        "greeting":        "Hi",
        "body":            lambda sn: f"Sprint <strong>{sn}</strong> has been completed. Here's a summary of what was delivered.",
        "done_label":      "Done",
        "carried_label":   "Carried Over",
        "points_label":    "Points Delivered",
        "sprint_label":    "Sprint",
        "project_label":   "Project",
        "footer":          "This is an automated message from Agile App.",
    },
    "hi": {
        "subtitle":        "स्प्रिंट पूरा हो गया 🏁",
        "greeting":        "नमस्ते",
        "body":            lambda sn: f"स्प्रिंट <strong>{sn}</strong> पूरा हो गया है। यहाँ एक सारांश है।",
        "done_label":      "पूर्ण",
        "carried_label":   "आगे बढ़ाया",
        "points_label":    "पॉइंट्स दिए गए",
        "sprint_label":    "स्प्रिंट",
        "project_label":   "प्रोजेक्ट",
        "footer":          "यह Agile App का स्वचालित संदेश है।",
    },
    "fr": {
        "subtitle":        "Sprint terminé 🏁",
        "greeting":        "Bonjour",
        "body":            lambda sn: f"Le sprint <strong>{sn}</strong> est terminé. Voici un résumé de ce qui a été livré.",
        "done_label":      "Terminés",
        "carried_label":   "Reportés",
        "points_label":    "Points livrés",
        "sprint_label":    "Sprint",
        "project_label":   "Projet",
        "footer":          "Ceci est un message automatique d'Agile App.",
    },
    "zh": {
        "subtitle":        "冲刺已完成 🏁",
        "greeting":        "您好",
        "body":            lambda sn: f"冲刺 <strong>{sn}</strong> 已完成。以下是交付成果摘要。",
        "done_label":      "已完成",
        "carried_label":   "已移回",
        "points_label":    "交付点数",
        "sprint_label":    "冲刺",
        "project_label":   "项目",
        "footer":          "这是来自 Agile App 的自动消息。",
    },
}

_SPRINT_COMPLETED_SUBJECTS = {
    "en": 'Sprint "{sprint}" completed — {done} done, {carried} carried over',
    "hi": 'स्प्रिंट "{sprint}" पूरा — {done} पूर्ण, {carried} आगे बढ़ाए',
    "fr": 'Sprint "{sprint}" terminé — {done} terminés, {carried} reportés',
    "zh": '冲刺"{sprint}"已完成 — {done}已完成，{carried}已移回',
}

def _build_sprint_completed_html(lang: str, username: str, sprint_name: str, project_name: str,done_count: int, carried_count: int, done_points: int,) -> str:
    c    = _SPRINT_COMPLETED_CONTENT[lang]
    stats = f"""
      <table width="100%"
             style="background:#f0fff4;border-radius:10px;border:1px solid #9ae6b4;
                    margin-bottom:24px;">
        <tr>
          {_stat_pill(c['done_label'],    str(done_count),    "#16a34a")}
          {_stat_pill(c['carried_label'], str(carried_count), "#d97706")}
          {_stat_pill(c['points_label'],  str(done_points),   "#6366f1")}
        </tr>
      </table>"""
    body = f"""
      <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">
        {c['greeting']} <strong>{username}</strong>,
      </p>
      <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
        {c['body'](sprint_name)}
      </p>
      {stats}
      {_card_box(_info_box(c['sprint_label'], sprint_name) + _info_box(c['project_label'], project_name))}"""
    return _base_email(
        header_gradient = "linear-gradient(135deg,#16a34a 0%,#15803d 100%)",
        header_emoji    = "🏁",
        header_subtitle = c["subtitle"],
        body_html       = body,
        footer_text     = c["footer"],
    )

_DEADLINE_CONFIGS = {
    "72h": {
        "gradient": "linear-gradient(135deg,#3b82f6,#1d4ed8)",
        "emoji":    "🗓️",
        "en": ("Deadline in 3 days",      "Heads up",      "is due in 72 hours",    "Due Date",    "Project", "This is an automated reminder from Agile App."),
        "hi": ("3 दिनों में समय-सीमा",   "ध्यान दें",    "72 घंटों में देय है",   "नियत तारीख", "प्रोजेक्ट", "यह Agile App का स्वचालित अनुस्मारक है।"),
        "fr": ("Échéance dans 3 jours",   "Attention",     "est dû dans 72 heures", "Échéance",    "Projet",   "Ceci est un rappel automatique d'Agile App."),
        "zh": ("3天后截止",                "注意",          "将在72小时后到期",       "截止日期",    "项目",     "这是来自 Agile App 的自动提醒。"),
    },
    "24h": {
        "gradient": "linear-gradient(135deg,#f59e0b,#d97706)",
        "emoji":    "⏰",
        "en": ("Due tomorrow",            "Due tomorrow",  "is due tomorrow",       "Due Date",    "Project", "This is an automated reminder from Agile App."),
        "hi": ("कल देय है",               "कल देय है",     "कल देय है",             "नियत तारीख", "प्रोजेक्ट", "यह Agile App का स्वचालित अनुस्मारक है।"),
        "fr": ("Dû demain",               "Dû demain",     "est dû demain",         "Échéance",    "Projet",   "Ceci est un rappel automatique d'Agile App."),
        "zh": ("明天到期",                  "明天到期",      "明天到期",               "截止日期",    "项目",     "这是来自 Agile App 的自动提醒。"),
    },
    "2h": {
        "gradient": "linear-gradient(135deg,#ea580c,#c2410c)",
        "emoji":    "🔥",
        "en": ("Due in 2 hours — act now", "Urgent",        "is due in 2 hours",     "Due Date",    "Project", "This is an automated reminder from Agile App."),
        "hi": ("2 घंटों में देय",          "अत्यावश्यक",   "2 घंटों में देय है",    "नियत तारीख", "प्रोजेक्ट", "यह Agile App का स्वचालित अनुस्मारक है।"),
        "fr": ("Dû dans 2 heures",         "Urgent",        "est dû dans 2 heures",  "Échéance",    "Projet",   "Ceci est un rappel automatique d'Agile App."),
        "zh": ("2小时后到期",               "紧急",          "将在2小时后到期",         "截止日期",    "项目",     "这是来自 Agile App 的自动提醒。"),
    },
}

_DEADLINE_SUBJECTS = {
    "72h": {
        "en": 'Reminder: "{issue}" is due in 72 hours',
        "hi": 'अनुस्मारक: "{issue}" 72 घंटों में देय है',
        "fr": 'Rappel : "{issue}" est dû dans 72 heures',
        "zh": '提醒："{issue}"将在72小时后到期',
    },
    "24h": {
        "en": 'Due tomorrow: "{issue}"',
        "hi": 'कल देय: "{issue}"',
        "fr": 'Dû demain : "{issue}"',
        "zh": '明天到期："{issue}"',
    },
    "2h": {
        "en": 'Due in 2 hours: "{issue}"',
        "hi": '2 घंटों में देय: "{issue}"',
        "fr": 'Dû dans 2 heures : "{issue}"',
        "zh": '2小时后到期："{issue}"',
    },
}

def _build_deadline_html(milestone: str, lang: str, username: str,issue_title: str, project_name: str, due_date: str,) -> str:
    cfg = _DEADLINE_CONFIGS[milestone]
    subtitle, urgency_word, due_phrase, due_label, proj_label, footer = cfg[lang]
    body = f"""
      <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">Hi <strong>{username}</strong>,</p>
      <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
        The issue <strong>"{issue_title}"</strong> in <strong>{project_name}</strong>
        {due_phrase}.
      </p>
      {_card_box(
          _info_box("Issue",       issue_title,  value_color="#1a202c") +
          _info_box(proj_label,    project_name, value_color="#4a5568") +
          _info_box(due_label,     due_date,     value_color="#4a5568")
      )}"""
    return _base_email(
        header_gradient = cfg["gradient"],
        header_emoji    = cfg["emoji"],
        header_subtitle = subtitle,
        body_html       = body,
        footer_text     = footer,
    )

_OVERDUE_CONTENT = {
    "en": {
        "subtitle":   "Issue Overdue 🚨",
        "footer":     "This is an automated notification from Agile App.",
        "assignee":   lambda t, p: f'The issue <strong>"{t}"</strong> in <strong>{p}</strong> has passed its deadline and is now <strong>overdue</strong>. Please update its status or notify your team.',
        "reporter":   lambda t, p: f'An issue you reported — <strong>"{t}"</strong> in <strong>{p}</strong> — has passed its deadline and is now <strong>overdue</strong>. You may want to follow up with the assignee.',
        "due_label":  "Was Due",
        "proj_label": "Project",
    },
    "hi": {
        "subtitle":   "इश्यू अतिदेय है 🚨",
        "footer":     "यह Agile App का स्वचालित संदेश है।",
        "assignee":   lambda t, p: f'<strong>{p}</strong> में इश्यू <strong>"{t}"</strong> की समय-सीमा बीत गई है और अब यह <strong>अतिदेय</strong> है।',
        "reporter":   lambda t, p: f'आपके द्वारा रिपोर्ट किया गया इश्यू <strong>"{t}"</strong> (<strong>{p}</strong>) अब <strong>अतिदेय</strong> है।',
        "due_label":  "समय-सीमा थी",
        "proj_label": "प्रोजेक्ट",
    },
    "fr": {
        "subtitle":   "Problème en retard 🚨",
        "footer":     "Ceci est une notification automatique d'Agile App.",
        "assignee":   lambda t, p: f'Le problème <strong>"{t}"</strong> dans <strong>{p}</strong> a dépassé son échéance et est maintenant <strong>en retard</strong>.',
        "reporter":   lambda t, p: f'Un problème que vous avez signalé — <strong>"{t}"</strong> dans <strong>{p}</strong> — est maintenant <strong>en retard</strong>.',
        "due_label":  "Était dû le",
        "proj_label": "Projet",
    },
    "zh": {
        "subtitle":   "问题已逾期 🚨",
        "footer":     "这是来自 Agile App 的自动通知。",
        "assignee":   lambda t, p: f'<strong>{p}</strong> 中的问题 <strong>"{t}"</strong> 已超过截止日期，目前<strong>逾期</strong>。',
        "reporter":   lambda t, p: f'您报告的问题 <strong>"{t}"</strong>（<strong>{p}</strong>）现已<strong>逾期</strong>。',
        "due_label":  "截止日期为",
        "proj_label": "项目",
    },
}

_OVERDUE_SUBJECTS = {
    "en": ('Overdue: "{issue}" has passed its deadline 🚨',  'Overdue issue you reported: "{issue}" 🚨'),
    "hi": ('अतिदेय: "{issue}" की समय-सीमा बीत गई 🚨',       'आपके द्वारा रिपोर्ट किया गया अतिदेय इश्यू: "{issue}" 🚨'),
    "fr": ('En retard : "{issue}" a dépassé l\'échéance 🚨',  'Problème en retard que vous avez signalé : "{issue}" 🚨'),
    "zh": ('已逾期："{issue}"已超过截止日期 🚨',               '您报告的逾期问题："{issue}" 🚨'),
}

def _build_overdue_html(lang: str, is_reporter: bool, username: str,issue_title: str, project_name: str, due_date: str,) -> str:
    c    = _OVERDUE_CONTENT[lang]
    body_text = c["reporter"](issue_title, project_name) if is_reporter else c["assignee"](issue_title, project_name)
    greeting  = {"en": "Hi", "hi": "नमस्ते", "fr": "Bonjour", "zh": "您好"}.get(lang, "Hi")
    body = f"""
      <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">
        {greeting} <strong>{username}</strong>,
      </p>
      <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">{body_text}</p>
      {_card_box(
          _info_box("Issue",         issue_title,  value_color="#1a202c",  label_color="#c53030") +
          _info_box(c['proj_label'], project_name, value_color="#4a5568",  label_color="#c53030") +
          _info_box(c['due_label'],  due_date,     value_color="#c53030",  label_color="#c53030"),
          bg="#fff5f5", border="#feb2b2"
      )}"""
    return _base_email(
        header_gradient = "linear-gradient(135deg,#dc2626,#b91c1c)",
        header_emoji    = "🚨",
        header_subtitle = c["subtitle"],
        body_html       = body,
        footer_text     = c["footer"],
    )

_SPRINT_ENDING_CONTENT = {
    "en": {
        "subtitle":       "Sprint ending in 2 days ⚠️",
        "greeting":       "Hi",
        "body":           lambda sn, n: f'Sprint <strong>{sn}</strong> ends in <strong>2 days</strong>. There are currently <strong>{n}</strong> incomplete issue(s) still in the sprint.',
        "sprint_label":   "Sprint",
        "project_label":  "Project",
        "ends_label":     "End Date",
        "open_label":     "Incomplete Issues",
        "footer":         "This is an automated reminder from Agile App.",
    },
    "hi": {
        "subtitle":       "स्प्रिंट 2 दिनों में समाप्त होगा ⚠️",
        "greeting":       "नमस्ते",
        "body":           lambda sn, n: f'स्प्रिंट <strong>{sn}</strong> <strong>2 दिनों</strong> में समाप्त होगा। अभी <strong>{n}</strong> अधूरे इश्यू बाकी हैं।',
        "sprint_label":   "स्प्रिंट",
        "project_label":  "प्रोजेक्ट",
        "ends_label":     "समाप्ति तारीख",
        "open_label":     "अधूरे इश्यू",
        "footer":         "यह Agile App का स्वचालित अनुस्मारक है।",
    },
    "fr": {
        "subtitle":       "Le sprint se termine dans 2 jours ⚠️",
        "greeting":       "Bonjour",
        "body":           lambda sn, n: f'Le sprint <strong>{sn}</strong> se termine dans <strong>2 jours</strong>. Il reste actuellement <strong>{n}</strong> problème(s) incomplet(s).',
        "sprint_label":   "Sprint",
        "project_label":  "Projet",
        "ends_label":     "Date de fin",
        "open_label":     "Problèmes incomplets",
        "footer":         "Ceci est un rappel automatique d'Agile App.",
    },
    "zh": {
        "subtitle":       "冲刺将在2天后结束 ⚠️",
        "greeting":       "您好",
        "body":           lambda sn, n: f'冲刺 <strong>{sn}</strong> 将在 <strong>2天</strong>后结束，目前还有 <strong>{n}</strong> 个未完成的问题。',
        "sprint_label":   "冲刺",
        "project_label":  "项目",
        "ends_label":     "结束日期",
        "open_label":     "未完成问题",
        "footer":         "这是来自 Agile App 的自动提醒。",
    },
}

_SPRINT_ENDING_SUBJECTS = {
    "en": 'Sprint "{sprint}" ends in 2 days — {open} issue(s) still incomplete',
    "hi": 'स्प्रिंट "{sprint}" 2 दिनों में समाप्त — {open} इश्यू अधूरे',
    "fr": 'Le sprint "{sprint}" se termine dans 2 jours — {open} problème(s) incomplet(s)',
    "zh": '冲刺"{sprint}"2天后结束 — {open}个问题未完成',
}

def _build_sprint_ending_html(lang: str, username: str, sprint_name: str, project_name: str,end_date: str, open_count: int,) -> str:
    c    = _SPRINT_ENDING_CONTENT[lang]
    body = f"""
      <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">
        {c['greeting']} <strong>{username}</strong>,
      </p>
      <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
        {c['body'](sprint_name, open_count)}
      </p>
      {_card_box(
          _info_box(c['sprint_label'],   sprint_name,       value_color="#1a202c") +
          _info_box(c['project_label'],  project_name,      value_color="#4a5568") +
          _info_box(c['ends_label'],     end_date,          value_color="#4a5568") +
          _info_box(c['open_label'],     str(open_count),   value_color="#d97706")
      )}"""
    return _base_email(
        header_gradient = "linear-gradient(135deg,#f59e0b,#d97706)",
        header_emoji    = "⚠️",
        header_subtitle = c["subtitle"],
        body_html       = body,
        footer_text     = c["footer"],
    )

def send_scrum_issue_assigned(email: str,username: str,issue_title: str,project_name: str,assigned_by: str,
                              language: str = "en",) -> bool:
    lang = language if language in _ASSIGNED_CONTENT else "en"
    subject = _ASSIGNED_SUBJECTS[lang].format(issue=issue_title)
    html = _build_assigned_html(lang, username, issue_title, project_name, assigned_by)
    return _send_email(email, subject, html)

def send_scrum_sprint_started(email: str,username: str,sprint_name: str,project_name: str,assigned_issues: List[str],
                              language: str = "en",) -> bool:
    lang = language if language in _SPRINT_STARTED_CONTENT else "en"
    subject = _SPRINT_STARTED_SUBJECTS[lang].format(sprint=sprint_name, count=len(assigned_issues))
    html = _build_sprint_started_html(lang, username, sprint_name, project_name, assigned_issues)
    return _send_email(email, subject, html)

def send_scrum_sprint_completed(email: str,username: str,sprint_name: str,project_name: str,done_count: int,
                                carried_count: int,done_points: int,language: str = "en",) -> bool:
    lang = language if language in _SPRINT_COMPLETED_CONTENT else "en"
    subject = _SPRINT_COMPLETED_SUBJECTS[lang].format(sprint=sprint_name, done=done_count, carried=carried_count)
    html = _build_sprint_completed_html(lang, username, sprint_name, project_name, done_count, carried_count, done_points)
    return _send_email(email, subject, html)

def send_scrum_issue_deadline_72h(email: str,username: str,issue_title: str,project_name: str,due_date: str,
                                  language: str = "en",) -> bool:
    lang = language if language in _DEADLINE_SUBJECTS["72h"] else "en"
    subject = _DEADLINE_SUBJECTS["72h"][lang].format(issue=issue_title)
    html = _build_deadline_html("72h", lang, username, issue_title, project_name, due_date)
    return _send_email(email, subject, html)

def send_scrum_issue_deadline_24h(email: str,username: str,issue_title: str,project_name: str,due_date: str,
                                  language: str = "en",) -> bool:
    lang = language if language in _DEADLINE_SUBJECTS["24h"] else "en"
    subject = _DEADLINE_SUBJECTS["24h"][lang].format(issue=issue_title)
    html = _build_deadline_html("24h", lang, username, issue_title, project_name, due_date)
    return _send_email(email, subject, html)

def send_scrum_issue_deadline_2h(email: str,username: str,issue_title: str,project_name: str,due_date: str,
                                 language: str = "en",) -> bool:
    lang = language if language in _DEADLINE_SUBJECTS["2h"] else "en"
    subject = _DEADLINE_SUBJECTS["2h"][lang].format(issue=issue_title)
    html = _build_deadline_html("2h", lang, username, issue_title, project_name, due_date)
    return _send_email(email, subject, html)

def send_scrum_issue_overdue_assignee(email: str,username: str,issue_title: str,project_name: str,due_date: str,
                                      language: str = "en",) -> bool:
    lang = language if language in _OVERDUE_CONTENT else "en"
    subject_tpl, _ = _OVERDUE_SUBJECTS[lang]
    subject = subject_tpl.format(issue=issue_title)
    html = _build_overdue_html(lang, False, username, issue_title, project_name, due_date)
    return _send_email(email, subject, html)

def send_scrum_issue_overdue_reporter(email: str,username: str,issue_title: str,project_name: str,
                                      due_date: str,language: str = "en",) -> bool:
    lang = language if language in _OVERDUE_CONTENT else "en"
    _, subject_tpl = _OVERDUE_SUBJECTS[lang]
    subject = subject_tpl.format(issue=issue_title)
    html = _build_overdue_html(lang, True, username, issue_title, project_name, due_date)
    return _send_email(email, subject, html)

def send_scrum_sprint_ending_soon(email: str,username: str,sprint_name: str,project_name: str,end_date: str,
                                  open_count: int,language: str = "en",) -> bool:
    lang = language if language in _SPRINT_ENDING_CONTENT else "en"
    subject = _SPRINT_ENDING_SUBJECTS[lang].format(sprint=sprint_name, open=open_count)
    html = _build_sprint_ending_html(lang, username, sprint_name, project_name, end_date, open_count)
    return _send_email(email, subject, html)

_REOPENED_CONTENT = {
    "en": {
        "subtitle": "Issue Reopened 🔄",
        "greeting": "Hi",
        "body": lambda t, p, by, status: (
            f'The issue <strong>"{t}"</strong> in project <strong>{p}</strong> '
            f'was moved back to <strong>{status}</strong> by <strong>{by}</strong>.'
        ),
        "issue_label": "Issue",
        "project_label": "Project",
        "status_label": "New Status",
        "footer": "This is an automated notification from Agile App.",
    },
    "hi": {
        "subtitle": "समस्या फिर से खोली गई 🔄",
        "greeting": "नमस्ते",
        "body": lambda t, p, by, status: (
            f'प्रोजेक्ट <strong>{p}</strong> में समस्या '
            f'<strong>"{t}"</strong> को <strong>{by}</strong> द्वारा '
            f'<strong>{status}</strong> में वापस ले जाया गया।'
        ),
        "issue_label": "समस्या",
        "project_label": "प्रोजेक्ट",
        "status_label": "नई स्थिति",
        "footer": "यह Agile App का स्वचालित संदेश है।",
    },
    "fr": {
        "subtitle": "Problème réouvert 🔄",
        "greeting": "Bonjour",
        "body": lambda t, p, by, status: (
            f'Le problème <strong>"{t}"</strong> du projet <strong>{p}</strong> '
            f'a été déplacé vers <strong>{status}</strong> par <strong>{by}</strong>.'
        ),
        "issue_label": "Problème",
        "project_label": "Projet",
        "status_label": "Nouveau statut",
        "footer": "Ceci est une notification automatique d'Agile App.",
    },
    "zh": {
        "subtitle": "问题已重新开启 🔄",
        "greeting": "您好",
        "body": lambda t, p, by, status: (
            f'项目 <strong>{p}</strong> 中的问题 '
            f'<strong>"{t}"</strong> 已被 <strong>{by}</strong> '
            f'移回 <strong>{status}</strong>。'
        ),
        "issue_label": "问题",
        "project_label": "项目",
        "status_label": "新状态",
        "footer": "这是来自 Agile App 的自动通知。",
    },
}

_REOPENED_SUBJECTS = {
    "en": 'Issue reopened: "{issue}"',
    "hi": 'समस्या फिर से खोली गई: "{issue}"',
    "fr": 'Problème réouvert : "{issue}"',
    "zh": '问题已重新开启："{issue}"',
}

def _build_reopened_html(lang: str,username: str,issue_title: str,project_name: str,reopened_by: str,new_status: str,) -> str:
    c = _REOPENED_CONTENT[lang]
    body = f"""
      <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">
        {c['greeting']} <strong>{username}</strong>,
      </p>

      <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
        {c['body'](issue_title, project_name, reopened_by, new_status)}
      </p>

      {_card_box(
          _info_box(c['issue_label'],   issue_title,  value_color="#1a202c") +
          _info_box(c['project_label'], project_name, value_color="#4a5568") +
          _info_box(c['status_label'],  new_status,   value_color="#d97706")
      )}
    """
    return _base_email(
        header_gradient="linear-gradient(135deg,#6366f1,#4f46e5)",
        header_emoji="🔄",
        header_subtitle=c["subtitle"],
        body_html=body,
        footer_text=c["footer"],
    )

def send_scrum_issue_reopened(email: str,username: str,issue_title: str,project_name: str,reopened_by: str,
                              new_status: str,language: str = "en",) -> bool:
    lang = language if language in _REOPENED_CONTENT else "en"
    subject = _REOPENED_SUBJECTS[lang].format(issue=issue_title)
    html = _build_reopened_html(lang,username,issue_title,project_name,reopened_by,new_status,)
    return _send_email(email, subject, html)