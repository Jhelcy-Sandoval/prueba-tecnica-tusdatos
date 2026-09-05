from playwright.async_api import Page


class G2UIHandler:
    '''
    Gestiona elementos de interfaz de usuario de G2.
    '''

    LOGIN_DIALOG = "dialog#login-overlay[open]"
    LOGIN_CLOSE_BUTTON = (
        'button[data-action="elv--modal-controller#close"]'
    )

    async def dismiss_login_overlay(self, page: Page) -> None:
        '''
        Cierra el modal de inicio de sesión cuando se encuentra
        visible en la página de G2.
        '''

        dialog = page.locator(self.LOGIN_DIALOG)

        if await dialog.count() == 0:
            return

        if not await dialog.is_visible():
            return

        close_button = dialog.locator(
            self.LOGIN_CLOSE_BUTTON
        )

        if await close_button.count() == 0:
            return

        await close_button.click()