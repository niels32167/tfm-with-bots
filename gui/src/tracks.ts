// The Global Parameter tracks as printed on the board. The engine enforces them; the GUI
// needs them only to draw the tracks.

export const MIN_TEMPERATURE = -30;
export const MAX_TEMPERATURE = 8;
export const TEMPERATURE_STEP = 2;
/** Reaching each of these Temperatures gives one heat Production. */
export const HEAT_PRODUCTION_BONUS_TEMPERATURES = [-24, -20];
/** Reaching this Temperature gives an Ocean to place. */
export const OCEAN_BONUS_TEMPERATURE = 0;

export const MAX_OXYGEN = 14;
/** Reaching this Oxygen level also raises Temperature one step. */
export const TEMPERATURE_BONUS_OXYGEN = 8;

export const MAX_OCEANS = 9;
