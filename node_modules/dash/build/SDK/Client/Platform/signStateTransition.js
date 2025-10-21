"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.signStateTransition = void 0;
/**
 *
 * @param {Platform} platform
 * @param {AbstractStateTransition} stateTransition
 * @param {Identity} identity
 * @param {number} [keyIndex]
 * @return {AbstractStateTransition}
 */
async function signStateTransition(platform, stateTransition, identity, keyIndex = 0) {
    const { client } = platform;
    const account = await client.getWalletAccount();
    const { privateKey } = account.identities.getIdentityHDKeyById(identity.getId().toString(), keyIndex);
    await stateTransition.sign(identity.getPublicKeyById(keyIndex), privateKey.toBuffer());
    return stateTransition;
}
exports.signStateTransition = signStateTransition;
//# sourceMappingURL=signStateTransition.js.map