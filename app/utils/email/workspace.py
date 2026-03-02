from app.utils.email.core import _send_email, _get_template

def _workspace_invite_html(name: str, code: str, admin: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px;
                    border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #4a5568;">You've been invited! 🎊</h2>
            <p><strong>{admin}</strong> has invited you to join the workspace:</p>
            <div style="background: #f7fafc; padding: 20px; border-radius: 8px;
                        margin: 24px 0; border: 1px solid #e2e8f0;">
                <h3 style="margin: 0 0 12px 0; color: #2d3748;">{name}</h3>
                <p style="margin: 0; color: #555;">Use this security code to join:</p>
                <div style="margin-top: 12px; text-align: center;">
                    <code style="background: #edf2f7; padding: 10px 20px; border-radius: 6px;
                                 font-size: 20px; letter-spacing: 4px; color: #2d3748;
                                 font-weight: bold;">{code}</code>
                </div>
            </div>
            <p style="color: #555;">Open Agile App, go to <strong>Join Workspace</strong>,
               enter the workspace ID and the code above.</p>
            <p style="color: #888; font-size: 13px;">If you were not expecting this invitation,
               you can safely ignore this email.</p>
        </div>
    </body>
    </html>
    """

_WORKSPACE_INVITE_TEMPLATES = {
    "en": _workspace_invite_html,
}

_WORKSPACE_INVITE_SUBJECTS = {
    "en": "You're invited to join {name} on Agile App",
}

def _workspace_welcome_html_en(username, workspace_name, workspace_description, admin_username,
                               member_count, joined_at):
    description_block = (
        f'<p style="color:#555;font-size:15px;margin:8px 0 0 0;">{workspace_description}</p>'
        if workspace_description else ""
    )
    return f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f6f8;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8;padding:40px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0"
                       style="background:#ffffff;border-radius:12px;
                              box-shadow:0 4px 16px rgba(0,0,0,0.08);overflow:hidden;">
                    <tr>
                        <td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                                   padding:40px;text-align:center;">
                            <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:700;">Agile App</h1>
                            <p style="margin:8px 0 0 0;color:rgba(255,255,255,0.85);font-size:15px;">
                                You've joined a workspace 🎉
                            </p>
                        </td>
                    </tr>
                    <tr><td style="padding:40px;">
                        <p style="margin:0 0 20px 0;color:#2d3748;font-size:16px;">
                            Hi <strong>{username}</strong>,
                        </p>
                        <p style="margin:0 0 28px 0;color:#555;font-size:15px;line-height:1.6;">
                            You have successfully joined a workspace on Agile App.
                            Here's everything you need to know to get started.
                        </p>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:28px;">
                            <tr><td style="padding:24px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    Workspace
                                </p>
                                <h2 style="margin:0;color:#1a202c;font-size:22px;font-weight:700;">
                                    {workspace_name}
                                </h2>
                                {description_block}
                            </td></tr>
                        </table>
                        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                            <tr>
                                <td width="50%" style="padding-right:8px;">
                                    <table width="100%" style="background:#f7fafc;border-radius:8px;
                                                               border:1px solid #e2e8f0;">
                                        <tr><td style="padding:16px;">
                                            <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                                      text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                                Admin
                                            </p>
                                            <p style="margin:0;color:#2d3748;font-size:15px;font-weight:600;">
                                                {admin_username}
                                            </p>
                                        </td></tr>
                                    </table>
                                </td>
                                <td width="50%" style="padding-left:8px;">
                                    <table width="100%" style="background:#f7fafc;border-radius:8px;
                                                               border:1px solid #e2e8f0;">
                                        <tr><td style="padding:16px;">
                                            <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                                      text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                                Team Size
                                            </p>
                                            <p style="margin:0;color:#2d3748;font-size:15px;font-weight:600;">
                                                {member_count} member{"s" if member_count != 1 else ""}
                                            </p>
                                        </td></tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        <table width="100%" style="background:#ebf8ff;border-radius:8px;
                                                   border:1px solid #bee3f8;margin-bottom:28px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#2b6cb0;font-size:14px;">
                                    ✅ <strong>Joined on</strong> {joined_at}
                                </p>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#fffff0;border-radius:8px;
                                                   border:1px solid #f6e05e;margin-bottom:32px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#744210;font-size:14px;">
                                    👤 You have been added as a <strong>member</strong>.
                                    Contact the workspace admin to change your role.
                                </p>
                            </td></tr>
                        </table>
                        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
                            Open Agile App to start collaborating with your team.
                        </p>
                    </td></tr>
                    <tr>
                        <td style="background:#f7fafc;padding:24px 40px;
                                   border-top:1px solid #e2e8f0;text-align:center;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
                                This is an automated message from Agile App.<br>
                                If you did not join this workspace, please contact support immediately.
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

def _workspace_welcome_html_hi(username, workspace_name, workspace_description, admin_username,
                               member_count, joined_at):
    description_block = (
        f'<p style="color:#555;font-size:15px;margin:8px 0 0 0;">{workspace_description}</p>'
        if workspace_description else ""
    )
    return f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f6f8;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8;padding:40px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0"
                       style="background:#ffffff;border-radius:12px;
                              box-shadow:0 4px 16px rgba(0,0,0,0.08);overflow:hidden;">
                    <tr>
                        <td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                                   padding:40px;text-align:center;">
                            <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:700;">Agile App</h1>
                            <p style="margin:8px 0 0 0;color:rgba(255,255,255,0.85);font-size:15px;">
                                आप एक वर्कस्पेस में शामिल हो गए 🎉
                            </p>
                        </td>
                    </tr>
                    <tr><td style="padding:40px;">
                        <p style="margin:0 0 20px 0;color:#2d3748;font-size:16px;">
                            नमस्ते <strong>{username}</strong>,
                        </p>
                        <p style="margin:0 0 28px 0;color:#555;font-size:15px;line-height:1.6;">
                            आप Agile App पर एक वर्कस्पेस में सफलतापूर्वक शामिल हो गए हैं।
                        </p>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:28px;">
                            <tr><td style="padding:24px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    वर्कस्पेस
                                </p>
                                <h2 style="margin:0;color:#1a202c;font-size:22px;font-weight:700;">
                                    {workspace_name}
                                </h2>
                                {description_block}
                            </td></tr>
                        </table>
                        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                            <tr>
                                <td width="50%" style="padding-right:8px;">
                                    <table width="100%" style="background:#f7fafc;border-radius:8px;
                                                               border:1px solid #e2e8f0;">
                                        <tr><td style="padding:16px;">
                                            <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                                      text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                                एडमिन
                                            </p>
                                            <p style="margin:0;color:#2d3748;font-size:15px;font-weight:600;">
                                                {admin_username}
                                            </p>
                                        </td></tr>
                                    </table>
                                </td>
                                <td width="50%" style="padding-left:8px;">
                                    <table width="100%" style="background:#f7fafc;border-radius:8px;
                                                               border:1px solid #e2e8f0;">
                                        <tr><td style="padding:16px;">
                                            <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                                      text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                                टीम साइज़
                                            </p>
                                            <p style="margin:0;color:#2d3748;font-size:15px;font-weight:600;">
                                                {member_count} सदस्य
                                            </p>
                                        </td></tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        <table width="100%" style="background:#ebf8ff;border-radius:8px;
                                                   border:1px solid #bee3f8;margin-bottom:28px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#2b6cb0;font-size:14px;">
                                    ✅ <strong>शामिल हुए:</strong> {joined_at}
                                </p>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#fffff0;border-radius:8px;
                                                   border:1px solid #f6e05e;margin-bottom:32px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#744210;font-size:14px;">
                                    👤 आपको <strong>सदस्य</strong> के रूप में जोड़ा गया है।
                                    रोल बदलने के लिए एडमिन से संपर्क करें।
                                </p>
                            </td></tr>
                        </table>
                        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
                            अपनी टीम के साथ सहयोग शुरू करने के लिए Agile App खोलें।
                        </p>
                    </td></tr>
                    <tr>
                        <td style="background:#f7fafc;padding:24px 40px;
                                   border-top:1px solid #e2e8f0;text-align:center;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
                                यह Agile App का स्वचालित संदेश है।<br>
                                यदि आप इस वर्कस्पेस में शामिल नहीं हुए, तो तुरंत सहायता से संपर्क करें।
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

def _workspace_welcome_html_fr(username, workspace_name, workspace_description, admin_username,
                               member_count, joined_at):
    description_block = (
        f'<p style="color:#555;font-size:15px;margin:8px 0 0 0;">{workspace_description}</p>'
        if workspace_description else ""
    )
    return f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f6f8;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8;padding:40px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0"
                       style="background:#ffffff;border-radius:12px;
                              box-shadow:0 4px 16px rgba(0,0,0,0.08);overflow:hidden;">
                    <tr>
                        <td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                                   padding:40px;text-align:center;">
                            <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:700;">Agile App</h1>
                            <p style="margin:8px 0 0 0;color:rgba(255,255,255,0.85);font-size:15px;">
                                Vous avez rejoint un espace de travail 🎉
                            </p>
                        </td>
                    </tr>
                    <tr><td style="padding:40px;">
                        <p style="margin:0 0 20px 0;color:#2d3748;font-size:16px;">
                            Bonjour <strong>{username}</strong>,
                        </p>
                        <p style="margin:0 0 28px 0;color:#555;font-size:15px;line-height:1.6;">
                            Vous avez rejoint avec succès un espace de travail sur Agile App.
                        </p>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:28px;">
                            <tr><td style="padding:24px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    Espace de travail
                                </p>
                                <h2 style="margin:0;color:#1a202c;font-size:22px;font-weight:700;">
                                    {workspace_name}
                                </h2>
                                {description_block}
                            </td></tr>
                        </table>
                        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                            <tr>
                                <td width="50%" style="padding-right:8px;">
                                    <table width="100%" style="background:#f7fafc;border-radius:8px;
                                                               border:1px solid #e2e8f0;">
                                        <tr><td style="padding:16px;">
                                            <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                                      text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                                Administrateur
                                            </p>
                                            <p style="margin:0;color:#2d3748;font-size:15px;font-weight:600;">
                                                {admin_username}
                                            </p>
                                        </td></tr>
                                    </table>
                                </td>
                                <td width="50%" style="padding-left:8px;">
                                    <table width="100%" style="background:#f7fafc;border-radius:8px;
                                                               border:1px solid #e2e8f0;">
                                        <tr><td style="padding:16px;">
                                            <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                                      text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                                Taille de l'équipe
                                            </p>
                                            <p style="margin:0;color:#2d3748;font-size:15px;font-weight:600;">
                                                {member_count} membre{"s" if member_count != 1 else ""}
                                            </p>
                                        </td></tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        <table width="100%" style="background:#ebf8ff;border-radius:8px;
                                                   border:1px solid #bee3f8;margin-bottom:28px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#2b6cb0;font-size:14px;">
                                    ✅ <strong>Rejoint le :</strong> {joined_at}
                                </p>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#fffff0;border-radius:8px;
                                                   border:1px solid #f6e05e;margin-bottom:32px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#744210;font-size:14px;">
                                    👤 Vous avez été ajouté(e) en tant que <strong>membre</strong>.
                                    Contactez l'administrateur pour changer votre rôle.
                                </p>
                            </td></tr>
                        </table>
                        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
                            Ouvrez Agile App pour commencer à collaborer avec votre équipe.
                        </p>
                    </td></tr>
                    <tr>
                        <td style="background:#f7fafc;padding:24px 40px;
                                   border-top:1px solid #e2e8f0;text-align:center;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
                                Ceci est un message automatique d'Agile App.<br>
                                Si vous n'avez pas rejoint cet espace, contactez le support immédiatement.
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

def _workspace_welcome_html_zh(username, workspace_name, workspace_description, admin_username,
                               member_count, joined_at):
    description_block = (
        f'<p style="color:#555;font-size:15px;margin:8px 0 0 0;">{workspace_description}</p>'
        if workspace_description else ""
    )
    return f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f6f8;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8;padding:40px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0"
                       style="background:#ffffff;border-radius:12px;
                              box-shadow:0 4px 16px rgba(0,0,0,0.08);overflow:hidden;">
                    <tr>
                        <td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                                   padding:40px;text-align:center;">
                            <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:700;">Agile App</h1>
                            <p style="margin:8px 0 0 0;color:rgba(255,255,255,0.85);font-size:15px;">
                                您已加入工作空间 🎉
                            </p>
                        </td>
                    </tr>
                    <tr><td style="padding:40px;">
                        <p style="margin:0 0 20px 0;color:#2d3748;font-size:16px;">
                            您好 <strong>{username}</strong>，
                        </p>
                        <p style="margin:0 0 28px 0;color:#555;font-size:15px;line-height:1.6;">
                            您已成功加入 Agile App 上的工作空间。
                        </p>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:28px;">
                            <tr><td style="padding:24px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    工作空间
                                </p>
                                <h2 style="margin:0;color:#1a202c;font-size:22px;font-weight:700;">
                                    {workspace_name}
                                </h2>
                                {description_block}
                            </td></tr>
                        </table>
                        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                            <tr>
                                <td width="50%" style="padding-right:8px;">
                                    <table width="100%" style="background:#f7fafc;border-radius:8px;
                                                               border:1px solid #e2e8f0;">
                                        <tr><td style="padding:16px;">
                                            <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                                      text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                                管理员
                                            </p>
                                            <p style="margin:0;color:#2d3748;font-size:15px;font-weight:600;">
                                                {admin_username}
                                            </p>
                                        </td></tr>
                                    </table>
                                </td>
                                <td width="50%" style="padding-left:8px;">
                                    <table width="100%" style="background:#f7fafc;border-radius:8px;
                                                               border:1px solid #e2e8f0;">
                                        <tr><td style="padding:16px;">
                                            <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                                      text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                                团队规模
                                            </p>
                                            <p style="margin:0;color:#2d3748;font-size:15px;font-weight:600;">
                                                {member_count} 位成员
                                            </p>
                                        </td></tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        <table width="100%" style="background:#ebf8ff;border-radius:8px;
                                                   border:1px solid #bee3f8;margin-bottom:28px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#2b6cb0;font-size:14px;">
                                    ✅ <strong>加入时间：</strong>{joined_at}
                                </p>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#fffff0;border-radius:8px;
                                                   border:1px solid #f6e05e;margin-bottom:32px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#744210;font-size:14px;">
                                    👤 您已被添加为<strong>成员</strong>。如需更改角色，请联系管理员。
                                </p>
                            </td></tr>
                        </table>
                        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
                            打开 Agile App，开始与您的团队协作。
                        </p>
                    </td></tr>
                    <tr>
                        <td style="background:#f7fafc;padding:24px 40px;
                                   border-top:1px solid #e2e8f0;text-align:center;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
                                这是来自 Agile App 的自动消息。<br>
                                如果您未加入此工作空间，请立即联系客服。
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

_WORKSPACE_WELCOME_TEMPLATES = {
    "en": _workspace_welcome_html_en,
    "hi": _workspace_welcome_html_hi,
    "fr": _workspace_welcome_html_fr,
    "zh": _workspace_welcome_html_zh,
}

_WORKSPACE_WELCOME_SUBJECTS = {
    "en": "Welcome to {name} on Agile App 🎉",
    "hi": "Agile App पर {name} में आपका स्वागत है 🎉",
    "fr": "Bienvenue dans {name} sur Agile App 🎉",
    "zh": "欢迎加入 Agile App 上的 {name} 🎉",
}

def workspace_invitation(email: str,name: str,code: str,admin: str,language: str = "en",) -> bool:
    subject = (_WORKSPACE_INVITE_SUBJECTS.get(language) or _WORKSPACE_INVITE_SUBJECTS["en"]).format(name=name)
    html = _get_template(_WORKSPACE_INVITE_TEMPLATES, language)(name, code, admin)
    return _send_email(email, subject, html)

def workspace_welcome(email: str,username: str,workspace_name: str,workspace_description: str,admin_username: str,
                      member_count: int,joined_at: str,language: str = "en",) -> bool:
    template_fn = _get_template(_WORKSPACE_WELCOME_TEMPLATES, language)
    html = template_fn(username, workspace_name, workspace_description,
                               admin_username, member_count, joined_at)
    subject_tpl = _WORKSPACE_WELCOME_SUBJECTS.get(language) or _WORKSPACE_WELCOME_SUBJECTS["en"]
    subject = subject_tpl.format(name=workspace_name)
    return _send_email(email, subject, html)

def _workspace_invite_new_user_html(name: str, code: str, admin: str) -> str:
    return f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f6f8;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background-color:#f4f6f8;padding:40px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0"
                       style="background:#ffffff;border-radius:12px;
                              box-shadow:0 4px 16px rgba(0,0,0,0.08);overflow:hidden;">
                    <tr>
                        <td style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                                   padding:40px;text-align:center;">
                            <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:700;">Agile App</h1>
                            <p style="margin:8px 0 0 0;color:rgba(255,255,255,0.85);font-size:15px;">
                                You've been invited to a workspace 🎊
                            </p>
                        </td>
                    </tr>
                    <tr><td style="padding:40px;">
                        <p style="margin:0 0 20px 0;color:#2d3748;font-size:16px;">
                            Hi there,
                        </p>
                        <p style="margin:0 0 20px 0;color:#555;font-size:15px;line-height:1.6;">
                            <strong>{admin}</strong> has invited you to join the workspace
                            <strong>{name}</strong> on Agile App.
                        </p>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:16px;">
                            <tr><td style="padding:20px 24px;">
                                <p style="margin:0 0 6px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    Step 1
                                </p>
                                <p style="margin:0;color:#1a202c;font-size:15px;font-weight:700;">
                                    Create your free Agile App account
                                </p>
                                <p style="margin:6px 0 0 0;color:#555;font-size:14px;line-height:1.5;">
                                    Visit <strong>agileapp.com</strong> and sign up using
                                    <strong>this email address</strong> so your invite is recognised automatically.
                                </p>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:24px;">
                            <tr><td style="padding:20px 24px;">
                                <p style="margin:0 0 6px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    Step 2
                                </p>
                                <p style="margin:0;color:#1a202c;font-size:15px;font-weight:700;">
                                    Join the workspace using this code
                                </p>
                                <p style="margin:6px 0 12px 0;color:#555;font-size:14px;">
                                    Go to <strong>Join Workspace</strong> in the app, enter the workspace name
                                    <strong>{name}</strong> and paste the code below:
                                </p>
                                <div style="text-align:center;">
                                    <code style="background:#edf2f7;padding:12px 24px;border-radius:8px;
                                                 font-size:22px;letter-spacing:6px;color:#2d3748;
                                                 font-weight:bold;display:inline-block;">{code}</code>
                                </div>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#fffff0;border-radius:8px;
                                                   border:1px solid #f6e05e;margin-bottom:32px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#744210;font-size:14px;">
                                    ⚠️ You must register with <strong>this email address</strong>
                                    for the invite to be recognised. Using a different address will require
                                    a new invite from the workspace admin.
                                </p>
                            </td></tr>
                        </table>
                        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
                            If you were not expecting this invitation, you can safely ignore this email.
                            No account will be created without your action.
                        </p>
                    </td></tr>
                    <tr>
                        <td style="background:#f7fafc;padding:24px 40px;
                                   border-top:1px solid #e2e8f0;text-align:center;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
                                This is an automated message from Agile App.<br>
                                Sent on behalf of <strong>{admin}</strong>.
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

def workspace_invitation_new_user(email: str, name: str, code: str, admin: str,) -> bool:
    subject = f"You're invited to join {name} on Agile App — create your account to get started"
    html = _workspace_invite_new_user_html(name, code, admin)
    return _send_email(email, subject, html)