class CaptchaProvider:
    """
    Proveedor de CAPTCHA de ejemplo.

    Esta clase representa el punto de integración con un
    servicio autorizado de resolución de CAPTCHA.
    """

    async def solve(self, page) -> bool:
        """
        Simula la integración con un proveedor externo.

        Retorna True si el proveedor indica que la
        verificación fue resuelta.
        """
        print("CAPTCHA detectado.")
        print("Se solicitaría la resolución al proveedor autorizado.")

        return False