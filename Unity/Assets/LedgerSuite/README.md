# Unity companion

`Runtime/ResonanceAudioZone.cs` is an optional UdonSharp component for applying
the near/far attenuation distances recorded in the Ledger Suite. Add it to the
audio emitter, assign the `AudioSource`, and set the zone distances in the
Inspector. The source must already be configured as a 3D audio source.

This component does not perform network calls, player tracking, moderation, or
access control. It expects Unity and the VRChat SDK/UdonSharp packages to be
installed in the consuming project; those packages are not bundled here.
