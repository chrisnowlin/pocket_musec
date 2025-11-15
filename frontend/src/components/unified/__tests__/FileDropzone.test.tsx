import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render } from '@testing-library/react';
import FileDropzone from '../FileDropzone';

describe('FileDropzone', () => {
  it('calls onDragActiveChange on drag over and drag leave', () => {
    const onDragActiveChange = vi.fn();
    const onDrop = vi.fn();
    const onFileSelect = vi.fn();
    const fileInputRef = { current: null } as React.RefObject<HTMLInputElement>;

    const { container, rerender } = render(
      <FileDropzone
        isActive={false}
        onDragActiveChange={onDragActiveChange}
        onDrop={onDrop}
        fileInputRef={fileInputRef}
        onFileSelect={onFileSelect}
        className="test-dropzone"
      >
        {() => <div>Drop content</div>}
      </FileDropzone>,
    );

    const dropzone = container.firstElementChild as HTMLElement;

    fireEvent.dragOver(dropzone);
    expect(onDragActiveChange).toHaveBeenCalledWith(true);

    // Re-render with isActive=true to simulate the state change
    rerender(
      <FileDropzone
        isActive={true}
        onDragActiveChange={onDragActiveChange}
        onDrop={onDrop}
        fileInputRef={fileInputRef}
        onFileSelect={onFileSelect}
        className="test-dropzone"
      >
        {() => <div>Drop content</div>}
      </FileDropzone>,
    );

    fireEvent.dragLeave(dropzone);
    expect(onDragActiveChange).toHaveBeenCalledWith(false);
  });

  it('calls onDrop when a drop event occurs', () => {
    const onDragActiveChange = vi.fn();
    const onDrop = vi.fn();
    const onFileSelect = vi.fn();
    const fileInputRef = { current: null } as React.RefObject<HTMLInputElement>;

    const { container } = render(
      <FileDropzone
        isActive={true}
        onDragActiveChange={onDragActiveChange}
        onDrop={onDrop}
        fileInputRef={fileInputRef}
        onFileSelect={onFileSelect}
      >
        {() => <div>Drop content</div>}
      </FileDropzone>,
    );

    const dropzone = container.firstElementChild as HTMLElement;

    fireEvent.drop(dropzone);
    expect(onDragActiveChange).toHaveBeenCalledWith(false);
    expect(onDrop).toHaveBeenCalledTimes(1);
  });

  it('calls onFileSelect when file input changes', () => {
    const onDragActiveChange = vi.fn();
    const onDrop = vi.fn();
    const onFileSelect = vi.fn();
    const fileInputRef = { current: null } as React.RefObject<HTMLInputElement>;

    const { container } = render(
      <FileDropzone
        isActive={false}
        onDragActiveChange={onDragActiveChange}
        onDrop={onDrop}
        fileInputRef={fileInputRef}
        onFileSelect={onFileSelect}
      >
        {() => <div>Drop content</div>}
      </FileDropzone>,
    );

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(input, { target: { files: [] } });
    expect(onFileSelect).toHaveBeenCalledTimes(1);
  });
});

