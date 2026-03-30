/**
 * Note: When using the Node.JS APIs, the config file
 * doesn't apply. Instead, pass options directly to the APIs.
 *
 * All configuration options: https://remotion.dev/docs/config
 */

import { Config } from "@remotion/cli/config";
import { enableTailwind } from '@remotion/tailwind-v4';

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.overrideWebpackConfig((currentConfig) => {
  const tailwindConfig = enableTailwind(currentConfig);
  return {
    ...tailwindConfig,
    // Fix: webpack FileSystemInfo uses wasm-hash internally on Node.js v22,
    // switching to memory cache bypasses the broken wasm hasher entirely.
    cache: {
      type: "memory",
    },
    output: {
      ...tailwindConfig.output,
      hashFunction: "xxhash64",
    },
  };
});
