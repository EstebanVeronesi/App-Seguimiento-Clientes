"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const util = require('util');
const winston = require('winston');
const LOG_LEVEL = process.env.LOG_LEVEL || 'info';
// Log levels:
//   error    0
//   warn     1
//   info     2  (default)
//   verbose  3
//   debug    4
//   silly    5
const createLogger = (formats = []) => winston.createLogger({
    level: LOG_LEVEL,
    transports: [
        new winston.transports.Console({
            format: winston.format.combine({
                transform: (info) => {
                    const args = info[Symbol.for('splat')];
                    const result = { ...info };
                    if (args) {
                        result.message = util.format(info.message, ...args);
                    }
                    return result;
                },
            }, ...formats, winston.format.colorize(), winston.format.printf(({ level, message, }) => `${level}: ${message}`)),
        }),
    ],
});
const logger = createLogger();
const loggers = {};
logger.getForId = (id) => {
    if (!loggers[id]) {
        const format = {
            transform: (info) => {
                const message = `[SDK: ${id}] ${info.message}`;
                return { ...info, message };
            },
        };
        loggers[id] = createLogger([format]);
    }
    return loggers[id];
};
logger.verbose(`[SDK] Logger uses "${LOG_LEVEL}" level`, { level: LOG_LEVEL });
exports.default = logger;
//# sourceMappingURL=index.js.map