Feature: Audio practices can record through QuickTime instead of raw ffmpeg
  Pronunciation and legato capture straight from the AVFoundation device by
  default: no macOS audio processing, so a quiet desk mic records a weak
  signal with the full noise floor. The learner's screen recordings prove
  the same mic sounds fine through QuickTime, whose chain applies the
  system mic mode, AGC and noise suppression before the file is written.
  recording.audio_recorder=quicktime puts the audio practices on that
  chain, with ffmpeg kept as the fallback when QuickTime automation fails.

  Scenario: Audio practices record through ffmpeg by default
    Given the default settings
    When a pronunciation session records its audio
    Then ffmpeg captures the take and QuickTime audio recording is never started

  Scenario: QuickTime records first when audio_recorder is quicktime
    Given recording.audio_recorder is set to quicktime
    When a pronunciation session records its audio
    Then QuickTime starts an audio recording and the ffmpeg capture is never constructed

  Scenario: A failed QuickTime start falls back to ffmpeg
    Given recording.audio_recorder is set to quicktime
    And QuickTime cannot start an audio recording
    When a pronunciation session records its audio
    Then the take is captured through ffmpeg instead and still saved
