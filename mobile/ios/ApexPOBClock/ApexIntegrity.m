#import <React/RCTBridgeModule.h>

// Bridges the Swift implementation into the React Native module registry.
@interface RCT_EXTERN_MODULE (ApexIntegrity, NSObject)

RCT_EXTERN_METHOD(getSignals:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject)

RCT_EXTERN_METHOD(requestAttestation:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject)

@end
