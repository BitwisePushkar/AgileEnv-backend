from app.utils.email.core import _send_email, _get_template

def _card_assigned_html_en(username, card_title, project_name, assigned_by):
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">
      <tr><td style="background:linear-gradient(135deg,#667eea,#764ba2);padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.85);font-size:15px;">You've been assigned to a card 📋</p>
      </td></tr>
      <tr><td style="padding:40px;">
        <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">Hi <strong>{username}</strong>,</p>
        <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
          <strong>{assigned_by}</strong> has assigned you to a card on the Kanban board.
          Head over to your board to view the details and get started.
        </p>
        <table width="100%" style="background:#f7fafc;border-radius:10px;border:1px solid #e2e8f0;margin-bottom:24px;">
          <tr><td style="padding:24px;">
            <p style="margin:0 0 4px;font-size:11px;color:#a0aec0;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Card</p>
            <h2 style="margin:0 0 16px;color:#1a202c;font-size:20px;">{card_title}</h2>
            <p style="margin:0 0 4px;font-size:11px;color:#a0aec0;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Project</p>
            <p style="margin:0;color:#4a5568;font-size:15px;font-weight:600;">{project_name}</p>
          </td></tr>
        </table>
        <table width="100%" style="background:#ebf8ff;border-radius:8px;border:1px solid #bee3f8;margin-bottom:32px;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0;color:#2b6cb0;font-size:14px;">👤 Assigned by <strong>{assigned_by}</strong></p>
          </td></tr>
        </table>
        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
          Open Agile App and go to the <strong>{project_name}</strong> Kanban board to see full details.
        </p>
      </td></tr>
      <tr><td style="background:#f7fafc;padding:24px 40px;border-top:1px solid #e2e8f0;text-align:center;">
        <p style="margin:0;color:#a0aec0;font-size:12px;">This is an automated message from Agile App.</p>
      </td></tr>
    </table></td></tr></table>
    </body></html>"""

def _card_assigned_html_hi(username, card_title, project_name, assigned_by):
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">
      <tr><td style="background:linear-gradient(135deg,#667eea,#764ba2);padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.85);font-size:15px;">आपको एक कार्ड सौंपा गया है 📋</p>
      </td></tr>
      <tr><td style="padding:40px;">
        <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">नमस्ते <strong>{username}</strong>,</p>
        <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
          <strong>{assigned_by}</strong> ने आपको Kanban बोर्ड पर एक कार्ड सौंपा है।
        </p>
        <table width="100%" style="background:#f7fafc;border-radius:10px;border:1px solid #e2e8f0;margin-bottom:24px;">
          <tr><td style="padding:24px;">
            <p style="margin:0 0 4px;font-size:11px;color:#a0aec0;text-transform:uppercase;letter-spacing:1px;font-weight:600;">कार्ड</p>
            <h2 style="margin:0 0 16px;color:#1a202c;font-size:20px;">{card_title}</h2>
            <p style="margin:0 0 4px;font-size:11px;color:#a0aec0;text-transform:uppercase;letter-spacing:1px;font-weight:600;">प्रोजेक्ट</p>
            <p style="margin:0;color:#4a5568;font-size:15px;font-weight:600;">{project_name}</p>
          </td></tr>
        </table>
        <table width="100%" style="background:#ebf8ff;border-radius:8px;border:1px solid #bee3f8;margin-bottom:32px;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0;color:#2b6cb0;font-size:14px;">👤 <strong>{assigned_by}</strong> द्वारा सौंपा गया</p>
          </td></tr>
        </table>
      </td></tr>
      <tr><td style="background:#f7fafc;padding:24px 40px;border-top:1px solid #e2e8f0;text-align:center;">
        <p style="margin:0;color:#a0aec0;font-size:12px;">यह Agile App का स्वचालित संदेश है।</p>
      </td></tr>
    </table></td></tr></table>
    </body></html>"""

def _card_assigned_html_fr(username, card_title, project_name, assigned_by):
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">
      <tr><td style="background:linear-gradient(135deg,#667eea,#764ba2);padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.85);font-size:15px;">Une carte vous a été assignée 📋</p>
      </td></tr>
      <tr><td style="padding:40px;">
        <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">Bonjour <strong>{username}</strong>,</p>
        <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
          <strong>{assigned_by}</strong> vous a assigné(e) à une carte sur le tableau Kanban.
        </p>
        <table width="100%" style="background:#f7fafc;border-radius:10px;border:1px solid #e2e8f0;margin-bottom:24px;">
          <tr><td style="padding:24px;">
            <p style="margin:0 0 4px;font-size:11px;color:#a0aec0;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Carte</p>
            <h2 style="margin:0 0 16px;color:#1a202c;font-size:20px;">{card_title}</h2>
            <p style="margin:0 0 4px;font-size:11px;color:#a0aec0;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Projet</p>
            <p style="margin:0;color:#4a5568;font-size:15px;font-weight:600;">{project_name}</p>
          </td></tr>
        </table>
        <table width="100%" style="background:#ebf8ff;border-radius:8px;border:1px solid #bee3f8;margin-bottom:32px;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0;color:#2b6cb0;font-size:14px;">👤 Assigné(e) par <strong>{assigned_by}</strong></p>
          </td></tr>
        </table>
      </td></tr>
      <tr><td style="background:#f7fafc;padding:24px 40px;border-top:1px solid #e2e8f0;text-align:center;">
        <p style="margin:0;color:#a0aec0;font-size:12px;">Ceci est un message automatique d'Agile App.</p>
      </td></tr>
    </table></td></tr></table>
    </body></html>"""

def _card_assigned_html_zh(username, card_title, project_name, assigned_by):
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">
      <tr><td style="background:linear-gradient(135deg,#667eea,#764ba2);padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.85);font-size:15px;">您被分配了一张卡片 📋</p>
      </td></tr>
      <tr><td style="padding:40px;">
        <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">您好 <strong>{username}</strong>，</p>
        <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
          <strong>{assigned_by}</strong> 在看板上将一张卡片分配给了您。
        </p>
        <table width="100%" style="background:#f7fafc;border-radius:10px;border:1px solid #e2e8f0;margin-bottom:24px;">
          <tr><td style="padding:24px;">
            <p style="margin:0 0 4px;font-size:11px;color:#a0aec0;text-transform:uppercase;letter-spacing:1px;font-weight:600;">卡片</p>
            <h2 style="margin:0 0 16px;color:#1a202c;font-size:20px;">{card_title}</h2>
            <p style="margin:0 0 4px;font-size:11px;color:#a0aec0;text-transform:uppercase;letter-spacing:1px;font-weight:600;">项目</p>
            <p style="margin:0;color:#4a5568;font-size:15px;font-weight:600;">{project_name}</p>
          </td></tr>
        </table>
        <table width="100%" style="background:#ebf8ff;border-radius:8px;border:1px solid #bee3f8;margin-bottom:32px;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0;color:#2b6cb0;font-size:14px;">👤 由 <strong>{assigned_by}</strong> 分配</p>
          </td></tr>
        </table>
      </td></tr>
      <tr><td style="background:#f7fafc;padding:24px 40px;border-top:1px solid #e2e8f0;text-align:center;">
        <p style="margin:0;color:#a0aec0;font-size:12px;">这是来自 Agile App 的自动消息。</p>
      </td></tr>
    </table></td></tr></table>
    </body></html>"""

_CARD_ASSIGNED_SUBJECTS = {
    "en": 'You\'ve been assigned to "{card}" on Agile App',
    "hi": 'Agile App पर "{card}" आपको सौंपा गया है',
    "fr": 'La carte "{card}" vous a été assignée sur Agile App',
    "zh": 'Agile App 上的卡片"{card}"已分配给您',
}
_CARD_ASSIGNED_TEMPLATES = {
    "en": _card_assigned_html_en,
    "hi": _card_assigned_html_hi,
    "fr": _card_assigned_html_fr,
    "zh": _card_assigned_html_zh,
}

def _card_completed_html_en(username, card_title, project_name, completed_by):
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">
      <tr><td style="background:linear-gradient(135deg,#16a34a,#15803d);padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.85);font-size:15px;">Your card has been completed ✅</p>
      </td></tr>
      <tr><td style="padding:40px;">
        <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">Hi <strong>{username}</strong>,</p>
        <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
          A card you created has been marked as <strong>completed</strong> by <strong>{completed_by}</strong>.
        </p>
        <table width="100%" style="background:#f0fff4;border-radius:10px;border:1px solid #9ae6b4;margin-bottom:24px;">
          <tr><td style="padding:24px;">
            <p style="margin:0 0 4px;font-size:11px;color:#276749;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Completed Card</p>
            <h2 style="margin:0 0 16px;color:#1a202c;font-size:20px;">{card_title}</h2>
            <p style="margin:0 0 4px;font-size:11px;color:#276749;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Project</p>
            <p style="margin:0;color:#4a5568;font-size:15px;font-weight:600;">{project_name}</p>
          </td></tr>
        </table>
        <table width="100%" style="background:#ebf8ff;border-radius:8px;border:1px solid #bee3f8;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0;color:#2b6cb0;font-size:14px;">✅ Marked done by <strong>{completed_by}</strong></p>
          </td></tr>
        </table>
      </td></tr>
      <tr><td style="background:#f7fafc;padding:24px 40px;border-top:1px solid #e2e8f0;text-align:center;">
        <p style="margin:0;color:#a0aec0;font-size:12px;">This is an automated message from Agile App.</p>
      </td></tr>
    </table></td></tr></table>
    </body></html>"""

def _card_completed_html_hi(username, card_title, project_name, completed_by):
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">
      <tr><td style="background:linear-gradient(135deg,#16a34a,#15803d);padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.85);font-size:15px;">आपका कार्ड पूरा हो गया ✅</p>
      </td></tr>
      <tr><td style="padding:40px;">
        <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">नमस्ते <strong>{username}</strong>,</p>
        <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
          आपके द्वारा बनाए गए एक कार्ड को <strong>{completed_by}</strong> ने पूर्ण किया।
        </p>
        <table width="100%" style="background:#f0fff4;border-radius:10px;border:1px solid #9ae6b4;margin-bottom:24px;">
          <tr><td style="padding:24px;">
            <p style="margin:0 0 4px;font-size:11px;color:#276749;text-transform:uppercase;letter-spacing:1px;font-weight:600;">पूर्ण कार्ड</p>
            <h2 style="margin:0 0 16px;color:#1a202c;font-size:20px;">{card_title}</h2>
            <p style="margin:0 0 4px;font-size:11px;color:#276749;text-transform:uppercase;letter-spacing:1px;font-weight:600;">प्रोजेक्ट</p>
            <p style="margin:0;color:#4a5568;font-size:15px;font-weight:600;">{project_name}</p>
          </td></tr>
        </table>
        <table width="100%" style="background:#ebf8ff;border-radius:8px;border:1px solid #bee3f8;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0;color:#2b6cb0;font-size:14px;">✅ <strong>{completed_by}</strong> द्वारा पूर्ण</p>
          </td></tr>
        </table>
      </td></tr>
      <tr><td style="background:#f7fafc;padding:24px 40px;border-top:1px solid #e2e8f0;text-align:center;">
        <p style="margin:0;color:#a0aec0;font-size:12px;">यह Agile App का स्वचालित संदेश है।</p>
      </td></tr>
    </table></td></tr></table>
    </body></html>"""

def _card_completed_html_fr(username, card_title, project_name, completed_by):
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">
      <tr><td style="background:linear-gradient(135deg,#16a34a,#15803d);padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.85);font-size:15px;">Votre carte a été complétée ✅</p>
      </td></tr>
      <tr><td style="padding:40px;">
        <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">Bonjour <strong>{username}</strong>,</p>
        <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
          Une carte que vous avez créée a été marquée <strong>terminée</strong> par <strong>{completed_by}</strong>.
        </p>
        <table width="100%" style="background:#f0fff4;border-radius:10px;border:1px solid #9ae6b4;margin-bottom:24px;">
          <tr><td style="padding:24px;">
            <p style="margin:0 0 4px;font-size:11px;color:#276749;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Carte terminée</p>
            <h2 style="margin:0 0 16px;color:#1a202c;font-size:20px;">{card_title}</h2>
            <p style="margin:0 0 4px;font-size:11px;color:#276749;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Projet</p>
            <p style="margin:0;color:#4a5568;font-size:15px;font-weight:600;">{project_name}</p>
          </td></tr>
        </table>
        <table width="100%" style="background:#ebf8ff;border-radius:8px;border:1px solid #bee3f8;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0;color:#2b6cb0;font-size:14px;">✅ Terminée par <strong>{completed_by}</strong></p>
          </td></tr>
        </table>
      </td></tr>
      <tr><td style="background:#f7fafc;padding:24px 40px;border-top:1px solid #e2e8f0;text-align:center;">
        <p style="margin:0;color:#a0aec0;font-size:12px;">Ceci est un message automatique d'Agile App.</p>
      </td></tr>
    </table></td></tr></table>
    </body></html>"""

def _card_completed_html_zh(username, card_title, project_name, completed_by):
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">
      <tr><td style="background:linear-gradient(135deg,#16a34a,#15803d);padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.85);font-size:15px;">您的卡片已完成 ✅</p>
      </td></tr>
      <tr><td style="padding:40px;">
        <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">您好 <strong>{username}</strong>，</p>
        <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
          您创建的卡片已被 <strong>{completed_by}</strong> 标记为完成。
        </p>
        <table width="100%" style="background:#f0fff4;border-radius:10px;border:1px solid #9ae6b4;margin-bottom:24px;">
          <tr><td style="padding:24px;">
            <p style="margin:0 0 4px;font-size:11px;color:#276749;text-transform:uppercase;letter-spacing:1px;font-weight:600;">已完成卡片</p>
            <h2 style="margin:0 0 16px;color:#1a202c;font-size:20px;">{card_title}</h2>
            <p style="margin:0 0 4px;font-size:11px;color:#276749;text-transform:uppercase;letter-spacing:1px;font-weight:600;">项目</p>
            <p style="margin:0;color:#4a5568;font-size:15px;font-weight:600;">{project_name}</p>
          </td></tr>
        </table>
        <table width="100%" style="background:#ebf8ff;border-radius:8px;border:1px solid #bee3f8;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0;color:#2b6cb0;font-size:14px;">✅ 由 <strong>{completed_by}</strong> 标记完成</p>
          </td></tr>
        </table>
      </td></tr>
      <tr><td style="background:#f7fafc;padding:24px 40px;border-top:1px solid #e2e8f0;text-align:center;">
        <p style="margin:0;color:#a0aec0;font-size:12px;">这是来自 Agile App 的自动消息。</p>
      </td></tr>
    </table></td></tr></table>
    </body></html>"""

_CARD_COMPLETED_SUBJECTS  = {
    "en": 'Your card "{card}" has been completed ✅',
    "hi": 'आपका कार्ड "{card}" पूरा हो गया ✅',
    "fr": 'Votre carte "{card}" a été complétée ✅',
    "zh": '您的卡片"{card}"已完成 ✅',
}
_CARD_COMPLETED_TEMPLATES = {
    "en": _card_completed_html_en,
    "hi": _card_completed_html_hi,
    "fr": _card_completed_html_fr,
    "zh": _card_completed_html_zh,
}

def _reminder_html(username: str,card_title: str,project_name: str,due_date: str,header_color: str,header_emoji: str,
                   header_line: str,greeting: str,body_line: str,due_label: str,project_label: str,footer_line: str,  ) -> str:
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">

      <!-- Header -->
      <tr><td style="background:{header_color};padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.9);font-size:15px;">{header_emoji} {header_line}</p>
      </td></tr>

      <!-- Body -->
      <tr><td style="padding:40px;">
        <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">{greeting} <strong>{username}</strong>,</p>
        <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">{body_line}</p>

        <!-- Card info box -->
        <table width="100%" style="background:#f7fafc;border-radius:10px;border:1px solid #e2e8f0;margin-bottom:24px;">
          <tr><td style="padding:24px;">
            <p style="margin:0 0 4px;font-size:11px;color:#a0aec0;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Card</p>
            <h2 style="margin:0 0 16px;color:#1a202c;font-size:20px;font-weight:700;">{card_title}</h2>
            <p style="margin:0 0 4px;font-size:11px;color:#a0aec0;text-transform:uppercase;letter-spacing:1px;font-weight:600;">{project_label}</p>
            <p style="margin:0 0 16px;color:#4a5568;font-size:15px;font-weight:600;">{project_name}</p>
            <p style="margin:0 0 4px;font-size:11px;color:#a0aec0;text-transform:uppercase;letter-spacing:1px;font-weight:600;">{due_label}</p>
            <p style="margin:0;color:#4a5568;font-size:15px;font-weight:600;">{due_date}</p>
          </td></tr>
        </table>
      </td></tr>

      <!-- Footer -->
      <tr><td style="background:#f7fafc;padding:24px 40px;border-top:1px solid #e2e8f0;text-align:center;">
        <p style="margin:0;color:#a0aec0;font-size:12px;">{footer_line}</p>
      </td></tr>

    </table></td></tr></table>
    </body></html>"""

def _overdue_html(username: str,card_title: str,project_name: str,due_date: str,is_creator: bool,greeting: str,
                  body_assignee: str,body_creator: str,overdue_label: str,project_label: str,footer_line: str,) -> str:
    body = body_creator if is_creator else body_assignee
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">
      <tr><td style="background:linear-gradient(135deg,#dc2626,#b91c1c);padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.9);font-size:15px;">🚨 {overdue_label}</p>
      </td></tr>
      <tr><td style="padding:40px;">
        <p style="margin:0 0 20px;color:#2d3748;font-size:16px;">{greeting} <strong>{username}</strong>,</p>
        <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">{body}</p>
        <table width="100%" style="background:#fff5f5;border-radius:10px;border:1px solid #feb2b2;margin-bottom:24px;">
          <tr><td style="padding:24px;">
            <p style="margin:0 0 4px;font-size:11px;color:#c53030;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Card</p>
            <h2 style="margin:0 0 16px;color:#1a202c;font-size:20px;font-weight:700;">{card_title}</h2>
            <p style="margin:0 0 4px;font-size:11px;color:#c53030;text-transform:uppercase;letter-spacing:1px;font-weight:600;">{project_label}</p>
            <p style="margin:0 0 16px;color:#4a5568;font-size:15px;font-weight:600;">{project_name}</p>
            <p style="margin:0 0 4px;font-size:11px;color:#c53030;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Was due</p>
            <p style="margin:0;color:#c53030;font-size:15px;font-weight:700;">{due_date}</p>
          </td></tr>
        </table>
      </td></tr>
      <tr><td style="background:#f7fafc;padding:24px 40px;border-top:1px solid #e2e8f0;text-align:center;">
        <p style="margin:0;color:#a0aec0;font-size:12px;">{footer_line}</p>
      </td></tr>
    </table></td></tr></table>
    </body></html>"""

def _card_reopened_html_en(username, card_title, project_name, column_name, reopened_by):
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">

      <tr><td style="background:linear-gradient(135deg,#6366f1,#4f46e5);padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.9);font-size:15px;">🔄 Card Reopened</p>
      </td></tr>

      <tr><td style="padding:40px;">
        <p>Hi <strong>{username}</strong>,</p>
        <p>
          The card <strong>"{card_title}"</strong> in project <strong>{project_name}</strong>
          was moved back to <strong>{column_name}</strong> by <strong>{reopened_by}</strong>.
        </p>

        <p style="margin-top:20px;color:#4338ca;">
          This card needs your attention again.
        </p>
      </td></tr>

      <tr><td style="background:#f7fafc;padding:24px;text-align:center;font-size:12px;color:#a0aec0;">
        This is an automated message from Agile App.
      </td></tr>

    </table></td></tr></table>
    </body></html>
    """

def _card_reopened_html_hi(username, card_title, project_name, column_name, reopened_by):
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">

      <tr><td style="background:linear-gradient(135deg,#6366f1,#4f46e5);padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.9);font-size:15px;">🔄 कार्ड पुनः खोला गया</p>
      </td></tr>

      <tr><td style="padding:40px;">
        <p>नमस्ते <strong>{username}</strong>,</p>
        <p>
          कार्ड <strong>"{card_title}"</strong> (प्रोजेक्ट: <strong>{project_name}</strong>)
          को <strong>{reopened_by}</strong> द्वारा फिर से <strong>{column_name}</strong> में भेजा गया है।
        </p>

        <p style="margin-top:20px;color:#4338ca;">
          इस कार्ड पर फिर से ध्यान देने की आवश्यकता है।
        </p>
      </td></tr>

      <tr><td style="background:#f7fafc;padding:24px;text-align:center;font-size:12px;color:#a0aec0;">
        यह Agile App द्वारा भेजा गया स्वचालित संदेश है।
      </td></tr>

    </table></td></tr></table>
    </body></html>
    """

def _card_reopened_html_fr(username, card_title, project_name, column_name, reopened_by):
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">

      <tr><td style="background:linear-gradient(135deg,#6366f1,#4f46e5);padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.9);font-size:15px;">🔄 Carte réouverte</p>
      </td></tr>

      <tr><td style="padding:40px;">
        <p>Bonjour <strong>{username}</strong>,</p>
        <p>
          La carte <strong>"{card_title}"</strong> du projet <strong>{project_name}</strong>
          a été déplacée vers <strong>{column_name}</strong> par <strong>{reopened_by}</strong>.
        </p>

        <p style="margin-top:20px;color:#4338ca;">
          Cette carte nécessite de nouveau votre attention.
        </p>
      </td></tr>

      <tr><td style="background:#f7fafc;padding:24px;text-align:center;font-size:12px;color:#a0aec0;">
        Ceci est un message automatique envoyé par Agile App.
      </td></tr>

    </table></td></tr></table>
    </body></html>
    """

def _card_reopened_html_zh(username, card_title, project_name, column_name, reopened_by):
    return f"""
    <html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
    <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
           style="background:#fff;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.08);overflow:hidden;">

      <tr><td style="background:linear-gradient(135deg,#6366f1,#4f46e5);padding:40px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;">Agile App</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,.9);font-size:15px;">🔄 卡片已重新开启</p>
      </td></tr>

      <tr><td style="padding:40px;">
        <p>您好 <strong>{username}</strong>,</p>
        <p>
          项目 <strong>{project_name}</strong> 中的卡片
          <strong>"{card_title}"</strong>
          已被 <strong>{reopened_by}</strong> 移回 <strong>{column_name}</strong>。
        </p>

        <p style="margin-top:20px;color:#4338ca;">
          该卡片需要您再次关注。
        </p>
      </td></tr>

      <tr><td style="background:#f7fafc;padding:24px;text-align:center;font-size:12px;color:#a0aec0;">
        此邮件由 Agile App 自动发送。
      </td></tr>

    </table></td></tr></table>
    </body></html>
    """

_REMINDER_72H = {
    "en": lambda u, c, p, d: (
        f'Reminder: "{c}" is due in 72 hours',
        _reminder_html(u, c, p, d,
            header_color = "linear-gradient(135deg,#3b82f6,#1d4ed8)",
            header_emoji = "🗓️",
            header_line = "Deadline in 3 days",
            greeting = "Hi",
            body_line = f'This is a heads-up that the card <strong>"{c}"</strong> on the <strong>{p}</strong> board is due in <strong>72 hours</strong>. Plan accordingly.',
            due_label = "Due Date",
            project_label = "Project",
            footer_line = "This is an automated reminder from Agile App.",
        ),
    ),
    "hi": lambda u, c, p, d: (
        f'अनुस्मारक: "{c}" की समय-सीमा 72 घंटों में है',
        _reminder_html(u, c, p, d,
            header_color = "linear-gradient(135deg,#3b82f6,#1d4ed8)",
            header_emoji = "🗓️",
            header_line = "3 दिनों में समय-सीमा",
            greeting = "नमस्ते",
            body_line = f'<strong>{p}</strong> बोर्ड पर कार्ड <strong>"{c}"</strong> की समय-सीमा <strong>72 घंटों</strong> में है। कृपया अनुसार योजना बनाएं।',
            due_label = "नियत तारीख",
            project_label = "प्रोजेक्ट",
            footer_line = "यह Agile App का स्वचालित अनुस्मारक है।",
        ),
    ),
    "fr": lambda u, c, p, d: (
        f'Rappel : "{c}" est dû dans 72 heures',
        _reminder_html(u, c, p, d,
            header_color  = "linear-gradient(135deg,#3b82f6,#1d4ed8)",
            header_emoji  = "🗓️",
            header_line   = "Échéance dans 3 jours",
            greeting      = "Bonjour",
            body_line     = f'La carte <strong>"{c}"</strong> du tableau <strong>{p}</strong> arrive à échéance dans <strong>72 heures</strong>. Planifiez en conséquence.',
            due_label     = "Échéance",
            project_label = "Projet",
            footer_line   = "Ceci est un rappel automatique d'Agile App.",
        ),
    ),
    "zh": lambda u, c, p, d: (
        f'提醒："{c}"将在72小时后到期',
        _reminder_html(u, c, p, d,
            header_color  = "linear-gradient(135deg,#3b82f6,#1d4ed8)",
            header_emoji  = "🗓️",
            header_line   = "3天后截止",
            greeting      = "您好",
            body_line     = f'<strong>{p}</strong> 看板上的卡片 <strong>"{c}"</strong> 将在 <strong>72小时</strong>后到期，请提前做好安排。',
            due_label     = "截止日期",
            project_label = "项目",
            footer_line   = "这是来自 Agile App 的自动提醒。",
        ),
    ),
}

_REMINDER_24H = {
    "en": lambda u, c, p, d: (
        f'Due tomorrow: "{c}"',
        _reminder_html(u, c, p, d,
            header_color  = "linear-gradient(135deg,#f59e0b,#d97706)",
            header_emoji  = "⏰",
            header_line   = "Due tomorrow",
            greeting      = "Hi",
            body_line     = f'The card <strong>"{c}"</strong> on the <strong>{p}</strong> board is due <strong>tomorrow</strong>. Make sure it\'s on track.',
            due_label     = "Due Date",
            project_label = "Project",
            footer_line   = "This is an automated reminder from Agile App.",
        ),
    ),
    "hi": lambda u, c, p, d: (
        f'कल देय है: "{c}"',
        _reminder_html(u, c, p, d,
            header_color  = "linear-gradient(135deg,#f59e0b,#d97706)",
            header_emoji  = "⏰",
            header_line   = "कल देय है",
            greeting      = "नमस्ते",
            body_line     = f'<strong>{p}</strong> बोर्ड पर कार्ड <strong>"{c}"</strong> <strong>कल</strong> देय है। सुनिश्चित करें कि यह सही रास्ते पर है।',
            due_label     = "नियत तारीख",
            project_label = "प्रोजेक्ट",
            footer_line   = "यह Agile App का स्वचालित अनुस्मारक है।",
        ),
    ),
    "fr": lambda u, c, p, d: (
        f'Dû demain : "{c}"',
        _reminder_html(u, c, p, d,
            header_color  = "linear-gradient(135deg,#f59e0b,#d97706)",
            header_emoji  = "⏰",
            header_line   = "Dû demain",
            greeting      = "Bonjour",
            body_line     = f'La carte <strong>"{c}"</strong> du tableau <strong>{p}</strong> est due <strong>demain</strong>. Assurez-vous qu\'elle avance bien.',
            due_label     = "Échéance",
            project_label = "Projet",
            footer_line   = "Ceci est un rappel automatique d'Agile App.",
        ),
    ),
    "zh": lambda u, c, p, d: (
        f'明天到期："{c}"',
        _reminder_html(u, c, p, d,
            header_color  = "linear-gradient(135deg,#f59e0b,#d97706)",
            header_emoji  = "⏰",
            header_line   = "明天截止",
            greeting      = "您好",
            body_line     = f'<strong>{p}</strong> 看板上的卡片 <strong>"{c}"</strong> <strong>明天</strong>到期，请确保进展顺利。',
            due_label     = "截止日期",
            project_label = "项目",
            footer_line   = "这是来自 Agile App 的自动提醒。",
        ),
    ),
}

_REMINDER_2H = {
    "en": lambda u, c, p, d: (
        f'Due in 2 hours: "{c}"',
        _reminder_html(u, c, p, d,
            header_color  = "linear-gradient(135deg,#ea580c,#c2410c)",
            header_emoji  = "🔥",
            header_line   = "Due in 2 hours — act now",
            greeting      = "Hi",
            body_line     = f'<strong>Urgent:</strong> The card <strong>"{c}"</strong> on the <strong>{p}</strong> board is due in <strong>2 hours</strong>.',
            due_label     = "Due Date",
            project_label = "Project",
            footer_line   = "This is an automated reminder from Agile App.",
        ),
    ),
    "hi": lambda u, c, p, d: (
        f'2 घंटों में देय: "{c}"',
        _reminder_html(u, c, p, d,
            header_color  = "linear-gradient(135deg,#ea580c,#c2410c)",
            header_emoji  = "🔥",
            header_line   = "2 घंटों में देय — अभी कार्रवाई करें",
            greeting      = "नमस्ते",
            body_line     = f'<strong>अत्यावश्यक:</strong> <strong>{p}</strong> बोर्ड पर कार्ड <strong>"{c}"</strong> <strong>2 घंटों</strong> में देय है।',
            due_label     = "नियत तारीख",
            project_label = "प्रोजेक्ट",
            footer_line   = "यह Agile App का स्वचालित अनुस्मारक है।",
        ),
    ),
    "fr": lambda u, c, p, d: (
        f'Dû dans 2 heures : "{c}"',
        _reminder_html(u, c, p, d,
            header_color  = "linear-gradient(135deg,#ea580c,#c2410c)",
            header_emoji  = "🔥",
            header_line   = "Dû dans 2 heures — agissez maintenant",
            greeting      = "Bonjour",
            body_line     = f'<strong>Urgent :</strong> La carte <strong>"{c}"</strong> du tableau <strong>{p}</strong> est due dans <strong>2 heures</strong>.',
            due_label     = "Échéance",
            project_label = "Projet",
            footer_line   = "Ceci est un rappel automatique d'Agile App.",
        ),
    ),
    "zh": lambda u, c, p, d: (
        f'2小时后到期："{c}"',
        _reminder_html(u, c, p, d,
            header_color  = "linear-gradient(135deg,#ea580c,#c2410c)",
            header_emoji  = "🔥",
            header_line   = "2小时后截止 — 请立即处理",
            greeting      = "您好",
            body_line     = f'<strong>紧急：</strong><strong>{p}</strong> 看板上的卡片 <strong>"{c}"</strong> 将在 <strong>2小时</strong>后到期。',
            due_label     = "截止日期",
            project_label = "项目",
            footer_line   = "这是来自 Agile App 的自动提醒。",
        ),
    ),
}

_OVERDUE_CONTENT = {
    "en": (
        "Card Overdue",
        "Hi",
        lambda c, p: f'The card <strong>"{c}"</strong> on the <strong>{p}</strong> board has passed its deadline and is now <strong>overdue</strong>. Please update the card status or contact your project manager.',
        lambda c, p: f'A card you created — <strong>"{c}"</strong> on the <strong>{p}</strong> board — has passed its deadline and is now <strong>overdue</strong>. You may want to follow up with the assignee.',
        "Project",
        "This is an automated notification from Agile App.",
    ),
    "hi": (
        "कार्ड की समय-सीमा समाप्त",
        "नमस्ते",
        lambda c, p: f'<strong>{p}</strong> बोर्ड पर कार्ड <strong>"{c}"</strong> की समय-सीमा बीत गई है और अब यह <strong>अतिदेय</strong> है। कृपया कार्ड की स्थिति अपडेट करें।',
        lambda c, p: f'आपके द्वारा बनाया गया कार्ड <strong>"{c}"</strong> (<strong>{p}</strong> बोर्ड) अब <strong>अतिदेय</strong> है। आप नियुक्त व्यक्ति से अनुवर्ती कार्रवाई कर सकते हैं।',
        "प्रोजेक्ट",
        "यह Agile App का स्वचालित संदेश है।",
    ),
    "fr": (
        "Carte en retard",
        "Bonjour",
        lambda c, p: f'La carte <strong>"{c}"</strong> du tableau <strong>{p}</strong> a dépassé son échéance et est maintenant <strong>en retard</strong>. Veuillez mettre à jour le statut ou contacter votre chef de projet.',
        lambda c, p: f'Une carte que vous avez créée — <strong>"{c}"</strong> du tableau <strong>{p}</strong> — est maintenant <strong>en retard</strong>. Vous pouvez faire un suivi avec la personne assignée.',
        "Projet",
        "Ceci est une notification automatique d'Agile App.",
    ),
    "zh": (
        "卡片已逾期",
        "您好",
        lambda c, p: f'<strong>{p}</strong> 看板上的卡片 <strong>"{c}"</strong> 已超过截止日期，目前<strong>逾期</strong>。请更新卡片状态或联系项目负责人。',
        lambda c, p: f'您创建的卡片 <strong>"{c}"</strong>（<strong>{p}</strong> 看板）现已<strong>逾期</strong>。您可以跟进负责人了解情况。',
        "项目",
        "这是来自 Agile App 的自动通知。",
    ),
}

_OVERDUE_SUBJECTS = {
    "en": ('Overdue: "{c}" has passed its deadline 🚨', 'Overdue card on your board: "{c}" 🚨'),
    "hi": ('अतिदेय: "{c}" की समय-सीमा बीत गई 🚨',     'आपके बोर्ड पर अतिदेय कार्ड: "{c}" 🚨'),
    "fr": ('En retard : "{c}" a dépassé l\'échéance 🚨', 'Carte en retard sur votre tableau : "{c}" 🚨'),
    "zh": ('已逾期："{c}"已超过截止日期 🚨',              '您看板上有逾期卡片："{c}" 🚨'),
}

def send_kanban_card_assigned(email: str, username: str, card_title: str,project_name: str, assigned_by: str, language: str = "en",) -> bool:
    lang = language if language in _CARD_ASSIGNED_TEMPLATES else "en"
    subject = _CARD_ASSIGNED_SUBJECTS[lang].format(card=card_title)
    html = _get_template(_CARD_ASSIGNED_TEMPLATES, lang)(username, card_title, project_name, assigned_by)
    return _send_email(email, subject, html)

def send_kanban_card_completed(email: str, username: str, card_title: str,project_name: str, completed_by: str, language: str = "en",) -> bool:
    lang = language if language in _CARD_COMPLETED_TEMPLATES else "en"
    subject = _CARD_COMPLETED_SUBJECTS[lang].format(card=card_title)
    html = _get_template(_CARD_COMPLETED_TEMPLATES, lang)(username, card_title, project_name, completed_by)
    return _send_email(email, subject, html)

def send_kanban_deadline_72h(email: str, username: str, card_title: str,project_name: str, due_date: str, language: str = "en",) -> bool:
    lang = language if language in _REMINDER_72H else "en"
    subject, html = _REMINDER_72H[lang](username, card_title, project_name, due_date)
    return _send_email(email, subject, html)

def send_kanban_deadline_24h(email: str, username: str, card_title: str, project_name: str, due_date: str, language: str = "en",) -> bool:
    lang = language if language in _REMINDER_24H else "en"
    subject, html = _REMINDER_24H[lang](username, card_title, project_name, due_date)
    return _send_email(email, subject, html)

def send_kanban_deadline_2h(email: str, username: str, card_title: str,project_name: str, due_date: str, language: str = "en",) -> bool:
    lang = language if language in _REMINDER_2H else "en"
    subject, html = _REMINDER_2H[lang](username, card_title, project_name, due_date)
    return _send_email(email, subject, html)

def send_kanban_overdue_assignee(email: str, username: str, card_title: str,project_name: str, due_date: str, language: str = "en",) -> bool:
    lang = language if language in _OVERDUE_CONTENT else "en"
    overdue_label, greeting, body_fn_a, _, project_label, footer = _OVERDUE_CONTENT[lang]
    subject_tpl, _ = _OVERDUE_SUBJECTS[lang]
    subject = subject_tpl.format(c=card_title)
    html = _overdue_html(username, card_title, project_name, due_date,is_creator = False,greeting = greeting,
                         body_assignee = body_fn_a(card_title, project_name),body_creator = "",overdue_label = overdue_label,
                         project_label = project_label,footer_line = footer,)
    return _send_email(email, subject, html)

def send_kanban_overdue_creator(email: str, username: str, card_title: str,project_name: str, due_date: str, language: str = "en",) -> bool:
    lang = language if language in _OVERDUE_CONTENT else "en"
    overdue_label, greeting, _, body_fn_c, project_label, footer = _OVERDUE_CONTENT[lang]
    _, subject_tpl = _OVERDUE_SUBJECTS[lang]
    subject = subject_tpl.format(c=card_title)
    html = _overdue_html(username, card_title, project_name, due_date,is_creator = True,greeting = greeting,
                         body_assignee = "",body_creator = body_fn_c(card_title, project_name),overdue_label = overdue_label,
                         project_label = project_label,footer_line = footer,)
    return _send_email(email, subject, html)

_CARD_REOPENED_SUBJECTS = {
    "en": 'Card reopened: "{card}"',
    "hi": 'कार्ड फिर से खोला गया: "{card}"',
    "fr": 'Carte réouverte : "{card}"',
    "zh": '卡片已重新开启："{card}"',
}

_CARD_REOPENED_TEMPLATES = {
    "en": _card_reopened_html_en,
    "hi": _card_reopened_html_hi,
    "fr": _card_reopened_html_fr,
    "zh": _card_reopened_html_zh,
}
def send_kanban_card_reopened(email: str,username: str,card_title: str,project_name: str,column_name: str,
                              reopened_by: str,language: str = "en",) -> bool:
    lang = language if language in _CARD_REOPENED_TEMPLATES else "en"
    subject = _CARD_REOPENED_SUBJECTS[lang].format(card=card_title)
    html = _get_template(_CARD_REOPENED_TEMPLATES, lang)(username,card_title,project_name,column_name,reopened_by,)
    return _send_email(email, subject, html)