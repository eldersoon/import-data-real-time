export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
};

export const formatDateTime = (dateString: string | null | undefined): string => {
  if (!dateString) return '-';
  
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('pt-BR', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(date);
  } catch {
    return dateString;
  }
};

export const calculateProgress = (processed: number, total: number | null): number => {
  if (!total || total === 0) return 0;
  return Math.round((processed / total) * 100);
};
