class HousekeepingService:
    def summarize(self) -> dict[str, str]:
        return {"status": "ready"}


housekeeping_service = HousekeepingService()
