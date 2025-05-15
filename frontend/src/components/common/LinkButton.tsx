// components/LinkButton.tsx
import React from "react";
import { Link } from "react-router-dom";
import type { LinkProps } from "react-router-dom";

type LinkButtonProps = LinkProps & {
  children: React.ReactNode;
  variant?: string;
  className?: string;
};

const LinkButton: React.FC<LinkButtonProps> = ({
  children,
  variant = "primary",
  className = "",
  ...props
}) => {
  return (
    <Link {...props} className={`btn btn-${variant} ${className}`}>
      {children}
    </Link>
  );
};

export default LinkButton;
