"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.creditWithdrawal = exports.STATUSES = void 0;
const dashcore_lib_1 = require("@dashevo/dashcore-lib");
const broadcastStateTransition_1 = __importDefault(require("../../broadcastStateTransition"));
const signStateTransition_1 = require("../../signStateTransition");
const fibonacci_1 = require("../../../../../utils/fibonacci");
exports.STATUSES = {
    PENDING: 0,
    POOLED: 1,
    BROADCASTED: 2,
    COMPLETED: 3,
};
// Implement remaining pooling types when they ready on drive side
const DEFAULT_POOLING = 0;
// TODO: add to dashcore-lib
// Asset unlock TX size is fixed with the default pooling
// since it has zero inputs and only one output
const ASSET_UNLOCK_TX_SIZE = 190;
// Minimal accepted core fee per byte to avoid low fee error from core
const MIN_ASSET_UNLOCK_CORE_FEE_PER_BYTE = 1;
// Minimal withdrawal amount in credits to avoid dust error from core
const MINIMAL_WITHDRAWAL_AMOUNT = ASSET_UNLOCK_TX_SIZE * MIN_ASSET_UNLOCK_CORE_FEE_PER_BYTE * 1000;
/** Creates platform credits withdrawal request
 * @param identity - identity to withdraw from
 * @param amount - amount of credits to withdraw
 * @param options - withdrawal options
 * @param [options] - withdrawal options
 * @param [options.toAddress] - withdrawal destination address
 */
async function creditWithdrawal(identity, amount, options = {}) {
    await this.initialize();
    // eslint-disable-next-line no-param-reassign
    options = {
        signingKeyIndex: 3,
        ...options,
    };
    const { dpp } = this;
    let outputScriptBytes;
    if (options.toAddress) {
        let toAddress;
        try {
            toAddress = new dashcore_lib_1.Address(options.toAddress, this.client.network);
        }
        catch (e) {
            throw new Error(`Invalid core recipient "${options.toAddress}" for network ${this.client.network}`);
        }
        const outputScript = dashcore_lib_1.Script.buildPublicKeyHashOut(toAddress);
        // @ts-ignore
        outputScriptBytes = outputScript.toBuffer();
        this.logger.debug(`[Identity#creditWithdrawal] credits withdrawal from ${identity.getId().toString()} to ${toAddress.toString()} with amount ${amount}`);
    }
    else {
        this.logger.debug(`[Identity#creditWithdrawal] credits withdrawal from ${identity.getId().toString()} to recent withdrawal address with amount ${amount}`);
    }
    const balance = identity.getBalance();
    if (amount > balance) {
        throw new Error(`Withdrawal amount "${amount}" is bigger that identity balance "${balance}"`);
    }
    if (amount < MINIMAL_WITHDRAWAL_AMOUNT) {
        throw new Error(`Withdrawal amount "${amount}" is less than minimal allowed withdrawal amount "${MINIMAL_WITHDRAWAL_AMOUNT}"`);
    }
    if (!this.client.wallet) {
        throw new Error('Wallet is not initialized');
    }
    // Divide by 1000 as stated in policy for GetDustThreshold
    // https://github.com/dashpay/dash/blob/master/src/policy/policy.cpp#L23
    const minRelayFeePerByte = Math.ceil(this.client.wallet.storage
        .getDefaultChainStore().state.fees.minRelay / 1000);
    const coreFeePerByte = fibonacci_1.nearestGreaterFibonacci(minRelayFeePerByte);
    const identityNonce = await this.nonceManager.bumpIdentityNonce(identity.getId());
    const identityCreditWithdrawalTransition = dpp.identity
        .createIdentityCreditWithdrawalTransition(identity.getId(), BigInt(amount), coreFeePerByte, DEFAULT_POOLING, outputScriptBytes, BigInt(identityNonce));
    this.logger.silly('[Identity#creditWithdrawal] Created IdentityCreditWithdrawalTransition');
    await signStateTransition_1.signStateTransition(this, identityCreditWithdrawalTransition, identity, options.signingKeyIndex);
    // Skipping validation because it's already done above
    const stateTransitionResult = await broadcastStateTransition_1.default(this, identityCreditWithdrawalTransition, {
        skipValidation: true,
    });
    this.logger.silly('[Identity#creditWithdrawal] Broadcasted IdentityCreditWithdrawalTransition');
    return stateTransitionResult.metadata;
}
exports.creditWithdrawal = creditWithdrawal;
exports.default = creditWithdrawal;
//# sourceMappingURL=creditWithdrawal.js.map