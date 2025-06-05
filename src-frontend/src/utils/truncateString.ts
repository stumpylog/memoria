export const truncateString = (text: string | undefined, maxLength: number) => {
  if (!text) return "N/A";
  if (text.length <= maxLength) return text;
  return `${text.substring(0, maxLength)}...`;
};
