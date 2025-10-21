"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const bls_1 = __importDefault(require("@dashevo/bls"));
const buffer_1 = require("buffer");
exports.default = async () => {
    const bls = await bls_1.default();
    return {
        validatePublicKey(publicKeyBuffer) {
            let pk;
            try {
                pk = bls.G1Element.fromBytes(Uint8Array.from(publicKeyBuffer));
            }
            catch (e) {
                return false;
            }
            finally {
                if (pk) {
                    pk.delete();
                }
            }
            return Boolean(pk);
        },
        sign(data, key) {
            const blsKey = bls.PrivateKey.fromBytes(Uint8Array.from(key), true);
            const signature = bls.BasicSchemeMPL.sign(blsKey, data);
            const result = buffer_1.Buffer.from(signature.serialize());
            signature.delete();
            blsKey.delete();
            return result;
        },
        verifySignature(signature, data, publicKey) {
            const { G1Element, G2Element, BasicSchemeMPL } = bls;
            const blsKey = G1Element.fromBytes(Uint8Array.from(publicKey));
            const blsSignature = G2Element.fromBytes(Uint8Array.from(signature));
            const result = BasicSchemeMPL.verify(blsKey, Uint8Array.from(data), blsSignature);
            blsKey.delete();
            blsSignature.delete();
            return result;
        },
    };
};
//# sourceMappingURL=getBlsAdapter.js.map