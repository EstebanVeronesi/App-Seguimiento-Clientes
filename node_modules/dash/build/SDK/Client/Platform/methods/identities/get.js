"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.get = void 0;
const wasm_dpp_1 = require("@dashevo/wasm-dpp");
const NotFoundError = require('@dashevo/dapi-client/lib/transport/GrpcTransport/errors/NotFoundError');
/**
 * Get an identity from the platform
 *
 * @param {Platform} this - bound instance class
 * @param {string|Identifier} id - id
 * @returns Identity
 */
async function get(id) {
    await this.initialize();
    const identifier = wasm_dpp_1.Identifier.from(id);
    let identityResponse;
    try {
        identityResponse = await this.fetcher.fetchIdentity(identifier);
    }
    catch (e) {
        if (e instanceof NotFoundError) {
            return null;
        }
        throw e;
    }
    const identity = this.dpp.identity.createFromBuffer(identityResponse.getIdentity());
    let metadata;
    const responseMetadata = identityResponse.getMetadata();
    if (responseMetadata) {
        metadata = new wasm_dpp_1.Metadata(responseMetadata.getHeight(), responseMetadata.getCoreChainLockedHeight(), responseMetadata.getTimeMs(), responseMetadata.getProtocolVersion());
    }
    identity.setMetadata(metadata);
    return identity;
}
exports.get = get;
exports.default = get;
//# sourceMappingURL=get.js.map