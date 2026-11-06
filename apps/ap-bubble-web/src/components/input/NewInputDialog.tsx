import { Modal, Text } from '@mantine/core';

import { InputForm } from './InputForm';

interface Props {
  opened: boolean;
  onClose: () => void;
  onAdded: () => void;
}

/** The input form in a dialog; closes once the input is queued. */
export function NewInputDialog({ opened, onClose, onAdded }: Props) {
  const added = () => {
    onAdded();
    onClose();
  };
  return (
    <Modal opened={opened} onClose={onClose} size="lg" title={<Text fw={600}>New input</Text>}>
      <InputForm onAdded={added} />
    </Modal>
  );
}
