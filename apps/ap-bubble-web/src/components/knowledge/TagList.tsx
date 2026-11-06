import { Badge, Group } from '@mantine/core';

export function TagList({ tags }: { tags: string[] }) {
  if (tags.length === 0) return null;
  return (
    <Group gap={4}>
      {tags.map((tag) => (
        <Badge key={tag} variant="default" size="sm" tt="none" fw={400}>
          {tag}
        </Badge>
      ))}
    </Group>
  );
}
