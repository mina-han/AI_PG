from abc import ABC, abstractmethod


class VoiceProvider(ABC):
    @abstractmethod
    def place_call(self, *, to_number: str, tts_text: str, webhook_base: str, incident_id: int) -> str:
        """
        Place an outbound call with TTS and DTMF gather.

        Returns provider-specific call id.
        """

    @abstractmethod
    def webhook_path(self) -> str:
        """Return the relative callback path for provider webhook registration."""



