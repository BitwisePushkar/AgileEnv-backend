from app.utils.email.core import _send_email, _get_template

ROLE_LABELS = {
    "en": {
        "viewer":  "Viewer  —  can view project content",
        "editor":  "Editor  —  can create and edit tasks",
        "manager": "Manager  —  full project control",
    },
    "hi": {
        "viewer":  "व्यूअर  —  प्रोजेक्ट सामग्री देख सकते हैं",
        "editor":  "एडिटर  —  कार्य बना और संपादित कर सकते हैं",
        "manager": "मैनेजर  —  पूर्ण प्रोजेक्ट नियंत्रण",
    },
    "fr": {
        "viewer":  "Lecteur  —  peut consulter le contenu du projet",
        "editor":  "Éditeur  —  peut créer et modifier des tâches",
        "manager": "Gestionnaire  —  contrôle total du projet",
    },
    "zh": {
        "viewer":  "查看者  —  可以查看项目内容",
        "editor":  "编辑者  —  可以创建和编辑任务",
        "manager": "管理者  —  拥有项目完整控制权",
    },
}

def _get_role_label(role: str, language: str) -> str:
    labels = ROLE_LABELS.get(language) or ROLE_LABELS["en"]
    return labels.get(role, role)

def _project_member_added_html_en(username: str, project_name: str,
                                   workspace_id: int, role: str) -> str:
    role_label = _get_role_label(role, "en")
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
                                You've been added to a project 🚀
                            </p>
                        </td>
                    </tr>
                    <tr><td style="padding:40px;">
                        <p style="margin:0 0 20px 0;color:#2d3748;font-size:16px;">
                            Hi <strong>{username}</strong>,
                        </p>
                        <p style="margin:0 0 28px 0;color:#555;font-size:15px;line-height:1.6;">
                            You have been added to a project on Agile App.
                            You can now access the project from your workspace dashboard.
                        </p>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:28px;">
                            <tr><td style="padding:24px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    Project
                                </p>
                                <h2 style="margin:0;color:#1a202c;font-size:22px;font-weight:700;">
                                    {project_name}
                                </h2>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#f0fff4;border-radius:8px;
                                                   border:1px solid #9ae6b4;margin-bottom:28px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#276749;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    Your Role
                                </p>
                                <p style="margin:0;color:#22543d;font-size:15px;font-weight:600;">
                                    {role_label}
                                </p>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#fffff0;border-radius:8px;
                                                   border:1px solid #f6e05e;margin-bottom:32px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#744210;font-size:14px;">
                                    💡 To change your role or leave the project, contact a project manager
                                    or your workspace admin.
                                </p>
                            </td></tr>
                        </table>
                        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
                            Open Agile App and navigate to workspace <strong>#{workspace_id}</strong>
                            to find your project and start collaborating.
                        </p>
                    </td></tr>
                    <tr>
                        <td style="background:#f7fafc;padding:24px 40px;
                                   border-top:1px solid #e2e8f0;text-align:center;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
                                This is an automated message from Agile App.<br>
                                If you believe this was a mistake, please contact your workspace admin.
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

def _project_member_added_html_hi(username: str, project_name: str,
                                   workspace_id: int, role: str) -> str:
    role_label = _get_role_label(role, "hi")
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
                                आपको एक प्रोजेक्ट में जोड़ा गया है 🚀
                            </p>
                        </td>
                    </tr>
                    <tr><td style="padding:40px;">
                        <p style="margin:0 0 20px 0;color:#2d3748;font-size:16px;">
                            नमस्ते <strong>{username}</strong>,
                        </p>
                        <p style="margin:0 0 28px 0;color:#555;font-size:15px;line-height:1.6;">
                            आपको Agile App पर एक प्रोजेक्ट में जोड़ा गया है।
                            अब आप अपने वर्कस्पेस डैशबोर्ड से प्रोजेक्ट एक्सेस कर सकते हैं।
                        </p>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:28px;">
                            <tr><td style="padding:24px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    प्रोजेक्ट
                                </p>
                                <h2 style="margin:0;color:#1a202c;font-size:22px;font-weight:700;">
                                    {project_name}
                                </h2>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#f0fff4;border-radius:8px;
                                                   border:1px solid #9ae6b4;margin-bottom:28px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#276749;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    आपकी भूमिका
                                </p>
                                <p style="margin:0;color:#22543d;font-size:15px;font-weight:600;">
                                    {role_label}
                                </p>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#fffff0;border-radius:8px;
                                                   border:1px solid #f6e05e;margin-bottom:32px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#744210;font-size:14px;">
                                    💡 अपनी भूमिका बदलने या प्रोजेक्ट छोड़ने के लिए किसी प्रोजेक्ट मैनेजर
                                    या अपने वर्कस्पेस एडमिन से संपर्क करें।
                                </p>
                            </td></tr>
                        </table>
                        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
                            Agile App खोलें और अपना प्रोजेक्ट खोजने के लिए वर्कस्पेस
                            <strong>#{workspace_id}</strong> पर जाएं।
                        </p>
                    </td></tr>
                    <tr>
                        <td style="background:#f7fafc;padding:24px 40px;
                                   border-top:1px solid #e2e8f0;text-align:center;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
                                यह Agile App का स्वचालित संदेश है।<br>
                                यदि आपको लगता है यह गलती से हुआ है, तो अपने वर्कस्पेस एडमिन से संपर्क करें।
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

def _project_member_added_html_fr(username: str, project_name: str,
                                   workspace_id: int, role: str) -> str:
    role_label = _get_role_label(role, "fr")
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
                                Vous avez été ajouté(e) à un projet 🚀
                            </p>
                        </td>
                    </tr>
                    <tr><td style="padding:40px;">
                        <p style="margin:0 0 20px 0;color:#2d3748;font-size:16px;">
                            Bonjour <strong>{username}</strong>,
                        </p>
                        <p style="margin:0 0 28px 0;color:#555;font-size:15px;line-height:1.6;">
                            Vous avez été ajouté(e) à un projet sur Agile App.
                            Vous pouvez désormais y accéder depuis le tableau de bord de votre espace de travail.
                        </p>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:28px;">
                            <tr><td style="padding:24px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    Projet
                                </p>
                                <h2 style="margin:0;color:#1a202c;font-size:22px;font-weight:700;">
                                    {project_name}
                                </h2>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#f0fff4;border-radius:8px;
                                                   border:1px solid #9ae6b4;margin-bottom:28px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#276749;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    Votre rôle
                                </p>
                                <p style="margin:0;color:#22543d;font-size:15px;font-weight:600;">
                                    {role_label}
                                </p>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#fffff0;border-radius:8px;
                                                   border:1px solid #f6e05e;margin-bottom:32px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#744210;font-size:14px;">
                                    💡 Pour modifier votre rôle ou quitter le projet, contactez un gestionnaire
                                    de projet ou votre administrateur d'espace de travail.
                                </p>
                            </td></tr>
                        </table>
                        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
                            Ouvrez Agile App et accédez à l'espace de travail <strong>#{workspace_id}</strong>
                            pour trouver votre projet et commencer à collaborer.
                        </p>
                    </td></tr>
                    <tr>
                        <td style="background:#f7fafc;padding:24px 40px;
                                   border-top:1px solid #e2e8f0;text-align:center;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
                                Ceci est un message automatique d'Agile App.<br>
                                Si vous pensez que c'est une erreur, contactez votre administrateur d'espace.
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

def _project_member_added_html_zh(username: str, project_name: str,
                                   workspace_id: int, role: str) -> str:
    role_label = _get_role_label(role, "zh")
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
                                您已被添加到一个项目 🚀
                            </p>
                        </td>
                    </tr>
                    <tr><td style="padding:40px;">
                        <p style="margin:0 0 20px 0;color:#2d3748;font-size:16px;">
                            您好 <strong>{username}</strong>，
                        </p>
                        <p style="margin:0 0 28px 0;color:#555;font-size:15px;line-height:1.6;">
                            您已被添加到 Agile App 上的一个项目中。
                            现在您可以从工作空间仪表板访问该项目。
                        </p>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:28px;">
                            <tr><td style="padding:24px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    项目
                                </p>
                                <h2 style="margin:0;color:#1a202c;font-size:22px;font-weight:700;">
                                    {project_name}
                                </h2>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#f0fff4;border-radius:8px;
                                                   border:1px solid #9ae6b4;margin-bottom:28px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#276749;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    您的角色
                                </p>
                                <p style="margin:0;color:#22543d;font-size:15px;font-weight:600;">
                                    {role_label}
                                </p>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#fffff0;border-radius:8px;
                                                   border:1px solid #f6e05e;margin-bottom:32px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#744210;font-size:14px;">
                                    💡 如需更改角色或退出项目，请联系项目管理者或工作空间管理员。
                                </p>
                            </td></tr>
                        </table>
                        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
                            打开 Agile App，进入工作空间 <strong>#{workspace_id}</strong>
                            查找您的项目并开始协作。
                        </p>
                    </td></tr>
                    <tr>
                        <td style="background:#f7fafc;padding:24px 40px;
                                   border-top:1px solid #e2e8f0;text-align:center;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
                                这是来自 Agile App 的自动消息。<br>
                                如果您认为这是误操作，请联系您的工作空间管理员。
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

_PROJECT_MEMBER_ADDED_TEMPLATES = {
    "en": _project_member_added_html_en,
    "hi": _project_member_added_html_hi,
    "fr": _project_member_added_html_fr,
    "zh": _project_member_added_html_zh,
}

_PROJECT_MEMBER_ADDED_SUBJECTS = {
    "en": "You've been added to {project} on Agile App 🚀",
    "hi": "आपको Agile App पर {project} में जोड़ा गया है 🚀",
    "fr": "Vous avez été ajouté(e) à {project} sur Agile App 🚀",
    "zh": "您已被添加到 Agile App 上的 {project} 🚀",
}

def _project_member_removed_html_en(username: str, project_name: str) -> str:
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
                        <td style="background:linear-gradient(135deg,#718096 0%,#4a5568 100%);
                                   padding:40px;text-align:center;">
                            <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:700;">Agile App</h1>
                            <p style="margin:8px 0 0 0;color:rgba(255,255,255,0.85);font-size:15px;">
                                Project membership update
                            </p>
                        </td>
                    </tr>
                    <tr><td style="padding:40px;">
                        <p style="margin:0 0 20px 0;color:#2d3748;font-size:16px;">
                            Hi <strong>{username}</strong>,
                        </p>
                        <p style="margin:0 0 28px 0;color:#555;font-size:15px;line-height:1.6;">
                            You have been removed from a project on Agile App.
                            You no longer have access to its content or tasks.
                        </p>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:28px;">
                            <tr><td style="padding:24px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    Project
                                </p>
                                <h2 style="margin:0;color:#1a202c;font-size:22px;font-weight:700;">
                                    {project_name}
                                </h2>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#fff5f5;border-radius:8px;
                                                   border:1px solid #fed7d7;margin-bottom:32px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#742a2a;font-size:14px;">
                                    ⚠️ If you believe this was done in error, please contact
                                    your workspace admin or a project manager to be re-added.
                                </p>
                            </td></tr>
                        </table>
                        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
                            You still have access to your workspace and any other projects
                            you are a member of.
                        </p>
                    </td></tr>
                    <tr>
                        <td style="background:#f7fafc;padding:24px 40px;
                                   border-top:1px solid #e2e8f0;text-align:center;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
                                This is an automated message from Agile App.<br>
                                Your workspace membership is not affected by this change.
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

def _project_member_removed_html_hi(username: str, project_name: str) -> str:
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
                        <td style="background:linear-gradient(135deg,#718096 0%,#4a5568 100%);
                                   padding:40px;text-align:center;">
                            <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:700;">Agile App</h1>
                            <p style="margin:8px 0 0 0;color:rgba(255,255,255,0.85);font-size:15px;">
                                प्रोजेक्ट सदस्यता अपडेट
                            </p>
                        </td>
                    </tr>
                    <tr><td style="padding:40px;">
                        <p style="margin:0 0 20px 0;color:#2d3748;font-size:16px;">
                            नमस्ते <strong>{username}</strong>,
                        </p>
                        <p style="margin:0 0 28px 0;color:#555;font-size:15px;line-height:1.6;">
                            आपको Agile App पर एक प्रोजेक्ट से हटा दिया गया है।
                            अब आपके पास उसकी सामग्री या कार्यों तक पहुंच नहीं है।
                        </p>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:28px;">
                            <tr><td style="padding:24px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    प्रोजेक्ट
                                </p>
                                <h2 style="margin:0;color:#1a202c;font-size:22px;font-weight:700;">
                                    {project_name}
                                </h2>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#fff5f5;border-radius:8px;
                                                   border:1px solid #fed7d7;margin-bottom:32px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#742a2a;font-size:14px;">
                                    ⚠️ यदि आपको लगता है यह गलती से हुआ है, तो दोबारा जोड़े जाने के लिए
                                    अपने वर्कस्पेस एडमिन या किसी प्रोजेक्ट मैनेजर से संपर्क करें।
                                </p>
                            </td></tr>
                        </table>
                        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
                            आपके वर्कस्पेस और अन्य प्रोजेक्ट जिनके आप सदस्य हैं, वे अप्रभावित हैं।
                        </p>
                    </td></tr>
                    <tr>
                        <td style="background:#f7fafc;padding:24px 40px;
                                   border-top:1px solid #e2e8f0;text-align:center;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
                                यह Agile App का स्वचालित संदेश है।<br>
                                इस बदलाव से आपकी वर्कस्पेस सदस्यता प्रभावित नहीं होती।
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

def _project_member_removed_html_fr(username: str, project_name: str) -> str:
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
                        <td style="background:linear-gradient(135deg,#718096 0%,#4a5568 100%);
                                   padding:40px;text-align:center;">
                            <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:700;">Agile App</h1>
                            <p style="margin:8px 0 0 0;color:rgba(255,255,255,0.85);font-size:15px;">
                                Mise à jour de votre appartenance au projet
                            </p>
                        </td>
                    </tr>
                    <tr><td style="padding:40px;">
                        <p style="margin:0 0 20px 0;color:#2d3748;font-size:16px;">
                            Bonjour <strong>{username}</strong>,
                        </p>
                        <p style="margin:0 0 28px 0;color:#555;font-size:15px;line-height:1.6;">
                            Vous avez été retiré(e) d'un projet sur Agile App.
                            Vous n'avez plus accès à son contenu ni à ses tâches.
                        </p>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:28px;">
                            <tr><td style="padding:24px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    Projet
                                </p>
                                <h2 style="margin:0;color:#1a202c;font-size:22px;font-weight:700;">
                                    {project_name}
                                </h2>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#fff5f5;border-radius:8px;
                                                   border:1px solid #fed7d7;margin-bottom:32px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#742a2a;font-size:14px;">
                                    ⚠️ Si vous pensez que c'est une erreur, contactez votre administrateur
                                    d'espace de travail ou un gestionnaire de projet pour être réajouté(e).
                                </p>
                            </td></tr>
                        </table>
                        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
                            Vous conservez l'accès à votre espace de travail et aux autres projets
                            dont vous êtes membre.
                        </p>
                    </td></tr>
                    <tr>
                        <td style="background:#f7fafc;padding:24px 40px;
                                   border-top:1px solid #e2e8f0;text-align:center;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
                                Ceci est un message automatique d'Agile App.<br>
                                Votre appartenance à l'espace de travail n'est pas affectée par ce changement.
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

def _project_member_removed_html_zh(username: str, project_name: str) -> str:
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
                        <td style="background:linear-gradient(135deg,#718096 0%,#4a5568 100%);
                                   padding:40px;text-align:center;">
                            <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:700;">Agile App</h1>
                            <p style="margin:8px 0 0 0;color:rgba(255,255,255,0.85);font-size:15px;">
                                项目成员资格更新
                            </p>
                        </td>
                    </tr>
                    <tr><td style="padding:40px;">
                        <p style="margin:0 0 20px 0;color:#2d3748;font-size:16px;">
                            您好 <strong>{username}</strong>，
                        </p>
                        <p style="margin:0 0 28px 0;color:#555;font-size:15px;line-height:1.6;">
                            您已被从 Agile App 上的一个项目中移除。
                            您将无法再访问该项目的内容或任务。
                        </p>
                        <table width="100%" style="background:#f7fafc;border-radius:10px;
                                                   border:1px solid #e2e8f0;margin-bottom:28px;">
                            <tr><td style="padding:24px;">
                                <p style="margin:0 0 4px 0;font-size:11px;color:#a0aec0;
                                          text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                    项目
                                </p>
                                <h2 style="margin:0;color:#1a202c;font-size:22px;font-weight:700;">
                                    {project_name}
                                </h2>
                            </td></tr>
                        </table>
                        <table width="100%" style="background:#fff5f5;border-radius:8px;
                                                   border:1px solid #fed7d7;margin-bottom:32px;">
                            <tr><td style="padding:16px 20px;">
                                <p style="margin:0;color:#742a2a;font-size:14px;">
                                    ⚠️ 如果您认为这是误操作，请联系工作空间管理员或项目管理者重新添加您。
                                </p>
                            </td></tr>
                        </table>
                        <p style="margin:0;color:#555;font-size:14px;line-height:1.6;">
                            您仍然可以访问工作空间以及您所属的其他项目。
                        </p>
                    </td></tr>
                    <tr>
                        <td style="background:#f7fafc;padding:24px 40px;
                                   border-top:1px solid #e2e8f0;text-align:center;">
                            <p style="margin:0;color:#a0aec0;font-size:12px;line-height:1.6;">
                                这是来自 Agile App 的自动消息。<br>
                                此更改不会影响您的工作空间成员资格。
                            </p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

_PROJECT_MEMBER_REMOVED_TEMPLATES = {
    "en": _project_member_removed_html_en,
    "hi": _project_member_removed_html_hi,
    "fr": _project_member_removed_html_fr,
    "zh": _project_member_removed_html_zh,
}

_PROJECT_MEMBER_REMOVED_SUBJECTS = {
    "en": "You've been removed from {project} on Agile App",
    "hi": "आपको Agile App पर {project} से हटा दिया गया है",
    "fr": "Vous avez été retiré(e) de {project} sur Agile App",
    "zh": "您已被从 Agile App 上的 {project} 中移除",
}

def send_project_member_added(email: str,username: str,project_name: str,workspace_id: int,role: str,
                              language: str = "en",) -> bool:
    subject_tpl = (_PROJECT_MEMBER_ADDED_SUBJECTS.get(language) or _PROJECT_MEMBER_ADDED_SUBJECTS["en"])
    subject = subject_tpl.format(project=project_name)
    template = _get_template(_PROJECT_MEMBER_ADDED_TEMPLATES, language)
    html = template(username, project_name, workspace_id, role)
    return _send_email(email, subject, html)

def send_project_member_removed(email: str,username: str,project_name: str,language: str = "en",) -> bool:
    subject_tpl = (_PROJECT_MEMBER_REMOVED_SUBJECTS.get(language) or _PROJECT_MEMBER_REMOVED_SUBJECTS["en"])
    subject = subject_tpl.format(project=project_name)
    template = _get_template(_PROJECT_MEMBER_REMOVED_TEMPLATES, language)
    html = template(username, project_name)
    return _send_email(email, subject, html)