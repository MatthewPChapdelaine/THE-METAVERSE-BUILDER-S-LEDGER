using UdonSharp;
using UnityEngine;

[UdonBehaviourSyncMode(BehaviourSyncMode.None)]
public class ResonanceAudioZone : UdonSharpBehaviour
{
    public AudioSource targetAudioSource;
    public float nearDistance = 1.5f;
    public float farDistance = 12f;

    void Start()
    {
        if (targetAudioSource == null)
        {
            Debug.LogWarning("[Ledger] Assign an AudioSource to ResonanceAudioZone.", this);
            return;
        }

        if (nearDistance <= 0f || farDistance <= nearDistance)
        {
            Debug.LogWarning(
                "[Ledger] Audio zone requires a positive near distance and a farther outer distance.",
                this
            );
            return;
        }

        targetAudioSource.minDistance = nearDistance;
        targetAudioSource.maxDistance = farDistance;
    }
}
