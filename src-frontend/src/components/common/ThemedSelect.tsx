// src/components/common/ThemedSelect.tsx
import type { GroupBase, Props as SelectProps } from "react-select";

import React from "react";
import Select from "react-select";

import { useTheme } from "../../hooks/useTheme";

// Function to generate react-select styles based on theme
const getSelectStyles = (isDarkMode: boolean) => ({
  control: (provided: any, state: any) => ({
    ...provided,
    backgroundColor: isDarkMode ? "#212529" : "#ffffff",
    borderColor: state.isFocused
      ? isDarkMode
        ? "#6ea8fe"
        : "#86b7fe"
      : isDarkMode
        ? "#495057"
        : "#dee2e6",
    boxShadow: state.isFocused
      ? `0 0 0 0.2rem ${isDarkMode ? "rgba(110, 168, 254, 0.25)" : "rgba(13, 110, 253, 0.25)"}`
      : "none",
    color: isDarkMode ? "#ffffff" : "#212529",
    "&:hover": {
      borderColor: state.isFocused
        ? isDarkMode
          ? "#6ea8fe"
          : "#86b7fe"
        : isDarkMode
          ? "#6c757d"
          : "#adb5bd",
    },
  }),
  menu: (provided: any) => ({
    ...provided,
    backgroundColor: isDarkMode ? "#343a40" : "#ffffff",
    border: `1px solid ${isDarkMode ? "#495057" : "#dee2e6"}`,
    boxShadow: isDarkMode
      ? "0 0.5rem 1rem rgba(0, 0, 0, 0.5)"
      : "0 0.5rem 1rem rgba(0, 0, 0, 0.15)",
  }),
  option: (provided: any, state: any) => ({
    ...provided,
    backgroundColor: state.isSelected
      ? isDarkMode
        ? "#0d6efd"
        : "#0d6efd"
      : state.isFocused
        ? isDarkMode
          ? "#495057"
          : "#f8f9fa"
        : "transparent",
    color: state.isSelected ? "#ffffff" : isDarkMode ? "#ffffff" : "#212529",
    "&:hover": {
      backgroundColor: state.isSelected
        ? isDarkMode
          ? "#0b5ed7"
          : "#0b5ed7"
        : isDarkMode
          ? "#495057"
          : "#f8f9fa",
    },
  }),
  multiValue: (provided: any) => ({
    ...provided,
    backgroundColor: isDarkMode ? "#495057" : "#e9ecef",
    border: `1px solid ${isDarkMode ? "#6c757d" : "#adb5bd"}`,
  }),
  multiValueLabel: (provided: any) => ({
    ...provided,
    color: isDarkMode ? "#ffffff" : "#495057",
  }),
  multiValueRemove: (provided: any) => ({
    ...provided,
    color: isDarkMode ? "#adb5bd" : "#6c757d",
    "&:hover": {
      backgroundColor: "#dc3545",
      color: "white",
    },
  }),
  placeholder: (provided: any) => ({
    ...provided,
    color: isDarkMode ? "#adb5bd" : "#6c757d",
  }),
  singleValue: (provided: any) => ({
    ...provided,
    color: isDarkMode ? "#ffffff" : "#212529",
  }),
  input: (provided: any) => ({
    ...provided,
    color: isDarkMode ? "#ffffff" : "#212529",
  }),
  noOptionsMessage: (provided: any) => ({
    ...provided,
    color: isDarkMode ? "#adb5bd" : "#6c757d",
  }),
  loadingMessage: (provided: any) => ({
    ...provided,
    color: isDarkMode ? "#adb5bd" : "#6c757d",
  }),
});

// Overload signatures for single and multi-select
function ThemedSelect<
  Option,
  IsMulti extends boolean = false,
  Group extends GroupBase<Option> = GroupBase<Option>,
>(props: SelectProps<Option, IsMulti, Group>): React.JSX.Element;

function ThemedSelect<Option>(
  props: SelectProps<Option, boolean, GroupBase<Option>>,
): React.JSX.Element {
  const { effectiveTheme } = useTheme();
  const isDarkMode = effectiveTheme === "dark";

  const themedStyles = getSelectStyles(isDarkMode);

  // Merge provided styles with themed styles
  const mergedStyles = {
    ...themedStyles,
    ...props.styles,
  };

  return <Select {...props} styles={mergedStyles} />;
}

export default ThemedSelect;
