/**
 * Punch selfie capture.
 *
 * Front camera only, no gallery. Letting an employee pick an existing photo
 * would defeat the entire point of the control — the photo has to be taken at
 * the moment of the punch, not chosen from the camera roll.
 */
import { launchCamera } from 'react-native-image-picker';

// Kept small on purpose: the server caps uploads at 2MB, warehouse data
// connections are often poor, and a face check does not need a 12MP frame.
const OPTIONS = {
  mediaType: 'photo',
  cameraType: 'front',
  includeBase64: true,
  saveToPhotos: false,
  maxWidth: 800,
  maxHeight: 800,
  quality: 0.7,
};

export class SelfieCancelled extends Error {
  constructor() {
    super('Photo cancelled');
    this.name = 'SelfieCancelled';
  }
}

export async function captureSelfie() {
  const result = await launchCamera(OPTIONS);

  if (result.didCancel) throw new SelfieCancelled();
  if (result.errorCode) {
    throw new Error(
      result.errorCode === 'camera_unavailable'
        ? 'No camera available on this device.'
        : result.errorMessage || 'Could not open the camera.',
    );
  }

  const asset = result.assets?.[0];
  if (!asset?.base64) throw new Error('The photo could not be read. Try again.');
  return asset.base64;
}
