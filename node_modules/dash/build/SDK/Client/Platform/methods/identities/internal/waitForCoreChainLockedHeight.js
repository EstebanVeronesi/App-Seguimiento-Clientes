"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.waitForCoreChainLockedHeight = void 0;
async function waitForCoreChainLockedHeight(expectedCoreHeight) {
    const platform = this;
    await platform.initialize();
    const interval = 5000;
    let isCanceled = false;
    let timeout;
    let coreChainLockedHeight = 0;
    const promise = new Promise((resolve, reject) => {
        async function obtainCoreChainLockedHeight() {
            try {
                const response = await platform.client.getDAPIClient().platform.getEpochsInfo(0, 1);
                const metadata = response.getMetadata();
                coreChainLockedHeight = metadata.getCoreChainLockedHeight();
            }
            catch (e) {
                reject(e);
                return;
            }
            if (coreChainLockedHeight >= expectedCoreHeight) {
                resolve();
                return;
            }
            if (!isCanceled) {
                timeout = setTimeout(obtainCoreChainLockedHeight, interval);
            }
        }
        obtainCoreChainLockedHeight();
    });
    function cancel() {
        if (timeout) {
            clearTimeout(timeout);
        }
        isCanceled = true;
    }
    return {
        promise,
        cancel,
    };
}
exports.waitForCoreChainLockedHeight = waitForCoreChainLockedHeight;
exports.default = waitForCoreChainLockedHeight;
//# sourceMappingURL=waitForCoreChainLockedHeight.js.map