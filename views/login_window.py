        # Start RFID scanning when the window is shown
        self.logger.info("LoginWindow shown, starting RFID scanning")
        self.start_rfid_scanning()

        # Focus the RFID input field
        self.rfid_input.setFocus() 