"use client";

import React from "react";
import { ActionButton, ActionButtonProps } from "./ActionButton";

/**
 * @deprecated Use ActionButton instead. LiquidGlassButton is retained for compatibility.
 */
export const LiquidGlassButton: React.FC<ActionButtonProps> = (props) => {
  return <ActionButton {...props} />;
};
