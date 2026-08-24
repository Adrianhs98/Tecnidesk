"""
Servicio: email_service

Integra con Resend para el envío de correos electrónicos transaccionales.
"""
import resend
from typing import Any
from starlette.concurrency import run_in_threadpool

from app.models.ticket import Ticket
from app.models.shop import Shop
from app.config import get_settings

settings = get_settings()

if settings.resend_api_key:
    resend.api_key = settings.resend_api_key

async def send_ticket_email(to_email: str, ticket: Ticket, shop: Shop) -> bool:
    """
    Envía un correo con la información del ticket usando Resend.
    
    Args:
        to_email: Dirección de destino.
        ticket: Modelo SQLAlchemy del Ticket.
        shop: Modelo SQLAlchemy del Taller (Shop).
        
    Returns:
        True si se envió correctamente, False si hubo error.
    """
    try:
        if not settings.resend_api_key:
            print("⚠️ RESEND_API_KEY no configurado, omitiendo envío de email real.")
            return False

        tracking_link = f"{settings.frontend_url.rstrip('/')}/tracking/{ticket.tracking_token}"
        
        # HTML design responsive & professional
        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="text-align: center; padding-bottom: 20px; border-bottom: 1px solid #eeeeee;">
                <h1 style="color: #333333; margin: 0; font-size: 24px;">{shop.business_name}</h1>
            </div>
            <div style="padding: 20px 0;">
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Hola.</p>
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Tu dispositivo <strong>{ticket.device_brand} {ticket.device_model}</strong> ha sido ingresado en <strong>{shop.business_name}</strong>.</p>
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Puedes ver el estado en vivo, diagnóstico y fotos haciendo clic en el siguiente botón:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{tracking_link}" style="background-color: #0070f3; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">Ver Estado de tu Reparación</a>
                </div>
                
                <p style="color: #777777; font-size: 14px; line-height: 1.5;">O copia y pega este enlace en tu navegador:<br><a href="{tracking_link}" style="color: #0070f3;">{tracking_link}</a></p>
            </div>
            <div style="text-align: center; padding-top: 20px; border-top: 1px solid #eeeeee; color: #999999; font-size: 12px;">
                Este es un mensaje automático de TecniDesk en representación de {shop.business_name}.
            </div>
        </div>
        """
        
        response = await run_in_threadpool(
            resend.Emails.send,
            {
                "from": settings.mail_from,
                "to": to_email,
                "subject": f"Ticket de Reparación Ingresado - {shop.business_name}",
                "html": html_body
            }
        )
        print(f"✅ Email enviado exitosamente vía Resend a {to_email}: {response}")
        return True
    
    except Exception as e:
        print(f"❌ Excepción crítica al enviar email con Resend a {to_email}: {str(e)}")
        # No tumbamos el proceso de creación de ticket por fallo del email
        return False


async def send_approval_email(to_email: str, ticket: Ticket, shop: Shop) -> bool:
    """
    Envía un email al taller cuando el cliente aprueba el presupuesto.

    Args:
        to_email: Dirección del taller (contact_email del shop).
        ticket: Modelo SQLAlchemy del Ticket.
        shop: Modelo SQLAlchemy del Taller (Shop).

    Returns:
        True si se envió correctamente, False si hubo error.
    """
    try:
        if not settings.resend_api_key:
            print("⚠️ RESEND_API_KEY no configurado, omitiendo envío de email de aprobación.")
            return False

        admin_link = f"{settings.frontend_url.rstrip('/')}/admin"
        cost_str = f"${float(ticket.total_cost):.2f}" if ticket.total_cost else "No especificado"

        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="text-align: center; padding-bottom: 20px; border-bottom: 1px solid #eeeeee;">
                <h1 style="color: #333333; margin: 0; font-size: 24px;">✅ Presupuesto Aprobado</h1>
            </div>
            <div style="padding: 20px 0;">
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">¡Buenas noticias! El cliente ha <strong>aprobado</strong> el presupuesto para la siguiente reparación:</p>

                <div style="background-color: #f8f9fa; border-radius: 8px; padding: 16px; margin: 16px 0;">
                    <p style="margin: 4px 0; color: #333;"><strong>Equipo:</strong> {ticket.device_brand} {ticket.device_model}</p>
                    <p style="margin: 4px 0; color: #333;"><strong>Diagnóstico:</strong> {ticket.diagnostic_notes or 'N/A'}</p>
                    <p style="margin: 4px 0; color: #333;"><strong>Presupuesto aprobado:</strong> {cost_str}</p>
                </div>

                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Puedes comenzar con la reparación. Accede al panel de administración para más detalles:</p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{admin_link}" style="background-color: #22c55e; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">Ir al Panel de Administración</a>
                </div>
            </div>
            <div style="text-align: center; padding-top: 20px; border-top: 1px solid #eeeeee; color: #999999; font-size: 12px;">
                Este es un mensaje automático de TecniDesk en representación de {shop.business_name}.
            </div>
        </div>
        """

        response = await run_in_threadpool(
            resend.Emails.send,
            {
                "from": settings.mail_from,
                "to": to_email,
                "subject": f"✅ Cliente aprobó el presupuesto - {ticket.device_brand} {ticket.device_model}",
                "html": html_body
            }
        )
        print(f"✅ Email de aprobación enviado a {to_email}: {response}")
        return True

    except Exception as e:
        print(f"❌ Error al enviar email de aprobación a {to_email}: {str(e)}")
        return False


async def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    """
    Envía un email para recuperar la contraseña.
    """
    try:
        if not settings.resend_api_key:
            print(f"⚠️ RESEND_API_KEY no configurado. Link de reset: {reset_link}")
            return False

        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="text-align: center; padding-bottom: 20px; border-bottom: 1px solid #eeeeee;">
                <h1 style="color: #333333; margin: 0; font-size: 24px;">Recupera tu contraseña - TecniDesk</h1>
            </div>
            <div style="padding: 20px 0;">
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Hola,</p>
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Hemos recibido una solicitud para restablecer tu contraseña. Haz clic en el siguiente enlace para crear una nueva:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background-color: #0070f3; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">Restablecer Contraseña</a>
                </div>
                
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Este enlace expirará en 1 hora. Si no solicitaste este cambio, puedes ignorar este correo.</p>
                <p style="color: #777777; font-size: 14px; line-height: 1.5;"><br>O copia este enlace:<br><a href="{reset_link}" style="color: #0070f3;">{reset_link}</a></p>
            </div>
            <div style="text-align: center; padding-top: 20px; border-top: 1px solid #eeeeee; color: #999999; font-size: 12px;">
                TecniDesk
            </div>
        </div>
        """

        response = await run_in_threadpool(
            resend.Emails.send,
            {
                "from": settings.mail_from,
                "to": to_email,
                "subject": "Recupera tu contraseña - TecniDesk",
                "html": html_body
            }
        )
        print(f"✅ Email de recuperación enviado a {to_email}: {response}")
        return True

    except Exception as e:
        print(f"❌ Error al enviar email de recuperación a {to_email}: {str(e)}")
        return False


async def send_quote_ready_email(email: str, tracking_url: str, device_model: str) -> bool:
    """
    Envía un correo al cliente avisando que el presupuesto de su equipo
    está listo para revisión y aprobación.

    Args:
        email:        Dirección del cliente (contact_email del customer).
        tracking_url: URL completa del portal de rastreo del cliente.
        device_model: Nombre/modelo del dispositivo en reparación.

    Returns:
        True si se envió correctamente, False si hubo error.
    """
    try:
        if not settings.resend_api_key:
            print(f"⚠️ RESEND_API_KEY no configurado. URL de rastreo: {tracking_url}")
            return False

        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="text-align: center; padding-bottom: 20px; border-bottom: 1px solid #eeeeee;">
                <h1 style="color: #333333; margin: 0; font-size: 24px;">🔧 Presupuesto Listo para Revisión</h1>
            </div>
            <div style="padding: 20px 0;">
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Hola,</p>
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">
                    Tenemos buenas noticias. El diagnóstico de tu equipo
                    <strong>{device_model}</strong> está listo y ya puedes revisar
                    el presupuesto de reparación.
                </p>

                <div style="background-color: #f8f9fa; border-left: 4px solid #0070f3; border-radius: 4px; padding: 16px; margin: 16px 0;">
                    <p style="margin: 0; color: #333333; font-size: 15px;">
                        Ingresa al portal de seguimiento para ver el diagnóstico completo,
                        el costo estimado y aprobar o rechazar la reparación.
                    </p>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{tracking_url}"
                       style="background-color: #0070f3; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">
                        Ver Presupuesto y Aprobar
                    </a>
                </div>

                <p style="color: #777777; font-size: 14px; line-height: 1.5;">
                    O copia y pega este enlace en tu navegador:<br>
                    <a href="{tracking_url}" style="color: #0070f3;">{tracking_url}</a>
                </p>

                <p style="color: #555555; font-size: 14px; line-height: 1.5;">
                    Si tienes alguna duda, no dudes en contactarnos directamente.
                </p>
            </div>
            <div style="text-align: center; padding-top: 20px; border-top: 1px solid #eeeeee; color: #999999; font-size: 12px;">
                Este es un mensaje automático de TecniDesk. Por favor no respondas a este correo.
            </div>
        </div>
        """

        response = await run_in_threadpool(
            resend.Emails.send,
            {
                "from": settings.mail_from,
                "to": email,
                "subject": f"🔧 Presupuesto listo para tu {device_model} - Revisión pendiente",
                "html": html_body
            }
        )
        print(f"✅ Email de presupuesto enviado a {email}: {response}")
        return True

    except Exception as e:
        print(f"❌ Error al enviar email de presupuesto a {email}: {str(e)}")
        return False


async def send_technician_credentials_email(to_email: str, password: str, shop_name: str, login_url: str) -> bool:
    """
    Envía un correo con las credenciales de acceso para un nuevo técnico.
    """
    try:
        if not settings.resend_api_key:
            print(f"⚠️ RESEND_API_KEY no configurado. Credenciales para {to_email}: {password}")
            return False

        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="text-align: center; padding-bottom: 20px; border-bottom: 1px solid #eeeeee;">
                <h1 style="color: #333333; margin: 0; font-size: 24px;">Acceso a TecniDesk - {shop_name}</h1>
            </div>
            <div style="padding: 20px 0;">
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Hola,</p>
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Se te ha dado acceso al sistema de gestión de taller <strong>{shop_name}</strong> en TecniDesk.</p>
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Tus credenciales de acceso son:</p>
                
                <div style="background-color: #f8f9fa; border-radius: 8px; padding: 16px; margin: 16px 0;">
                    <p style="margin: 4px 0; color: #333;"><strong>Email:</strong> {to_email}</p>
                    <p style="margin: 4px 0; color: #333;"><strong>Contraseña:</strong> {password}</p>
                </div>
                
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Te recomendamos cambiar tu contraseña una vez que ingreses al sistema.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{login_url}" style="background-color: #0070f3; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">Iniciar Sesión</a>
                </div>
                
                <p style="color: #777777; font-size: 14px; line-height: 1.5;">O copia y pega este enlace en tu navegador:<br><a href="{login_url}" style="color: #0070f3;">{login_url}</a></p>
            </div>
            <div style="text-align: center; padding-top: 20px; border-top: 1px solid #eeeeee; color: #999999; font-size: 12px;">
                Este es un mensaje automático de TecniDesk.
            </div>
        </div>
        """

        response = await run_in_threadpool(
            resend.Emails.send,
            {
                "from": settings.mail_from,
                "to": to_email,
                "subject": f"Credenciales de acceso - {shop_name}",
                "html": html_body
            }
        )
        print(f"✅ Email de credenciales enviado a {to_email}: {response}")
        return True

    except Exception as e:
        print(f"❌ Error al enviar email de credenciales a {to_email}: {str(e)}")
        # Raise an error instead of returning false because we want it to fail the transaction
        raise e

