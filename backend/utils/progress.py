"""Progress indicators for long-running operations"""

import time
import threading
from typing import Optional, Callable, Any
from dataclasses import dataclass
from contextlib import contextmanager

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from rich.align import Align

console = Console()


@dataclass
class ProgressConfig:
    """Configuration for progress indicators"""
    show_spinner: bool = True
    show_percentage: bool = True
    show_time: bool = True
    show_speed: bool = False
    refresh_rate: float = 0.1
    description: str = "Processing..."
    total: Optional[int] = None


class ProgressIndicator:
    """Enhanced progress indicator with multiple display modes"""
    
    def __init__(self, config: Optional[ProgressConfig] = None):
        self.config = config or ProgressConfig()
        self.progress = None
        self.task_id = None
        self.live = None
        self.start_time = None
        self.is_running = False
        
    def start(self, description: Optional[str] = None, total: Optional[int] = None):
        """Start the progress indicator"""
        if description:
            self.config.description = description
        if total is not None:
            self.config.total = total
            
        self.start_time = time.time()
        self.is_running = True
        
        # Build progress columns dynamically
        columns = []
        if self.config.show_spinner:
            columns.append(SpinnerColumn())
        columns.append(TextColumn("[progress.description]{task.description}"))
        if self.config.total:
            columns.append(BarColumn())
        if self.config.show_percentage and self.config.total:
            columns.append(TaskProgressColumn())
        if self.config.show_time:
            columns.append(TimeElapsedColumn())
        
        # Create progress display
        self.progress = Progress(
            *columns,
            console=console,
            refresh_per_second=1/self.config.refresh_rate
        )
        
        self.task_id = self.progress.add_task(
            self.config.description,
            total=self.config.total
        )
        
    def update(self, advance: int = 1, description: Optional[str] = None):
        """Update progress"""
        if not self.is_running or not self.progress or not self.task_id:
            return
            
        if description:
            self.config.description = description
            self.progress.update(self.task_id, description=description)
            
        if self.config.total:
            self.progress.advance(self.task_id, advance)
            
    def finish(self, description: str = "Complete!"):
        """Mark progress as complete"""
        if not self.is_running:
            return
            
        if self.progress and self.task_id:
            completed_total = self.config.total if self.config.total is not None else 100
            self.progress.update(self.task_id, description=description, completed=completed_total)
            
        self.is_running = False
        
    def stop(self):
        """Stop the progress indicator"""
        self.is_running = False
        if self.progress:
            self.progress.stop()
            
    @contextmanager
    def progress_context(self, description: str = None, total: int = None):
        """Context manager for automatic progress handling"""
        try:
            self.start(description, total)
            yield self
        finally:
            self.finish()


class MultiStepProgress:
    """Progress indicator for multi-step operations"""
    
    def __init__(self, steps: list[str]):
        self.steps = steps
        self.current_step = 0
        self.progress = ProgressIndicator()
        
    def start_step(self, step_index: int = 0):
        """Start a specific step"""
        if 0 <= step_index < len(self.steps):
            self.current_step = step_index
            description = f"Step {step_index + 1}/{len(self.steps)}: {self.steps[step_index]}"
            self.progress.start(description, total=100)
            
    def next_step(self):
        """Move to next step"""
        self.current_step += 1
        if self.current_step < len(self.steps):
            self.start_step(self.current_step)
            
    def update_current_step(self, progress: int):
        """Update progress within current step"""
        self.progress.update(advance=progress)
        
    def finish_current_step(self):
        """Finish current step and move to next"""
        self.progress.finish(f"✅ Step {self.current_step + 1}/{len(self.steps)}: {self.steps[self.current_step]}")
        self.progress.stop()
        self.next_step()


class AnimatedProgress:
    """Animated progress indicator for indeterminate operations"""
    
    def __init__(self, description: str = "Working..."):
        self.description = description
        self.is_running = False
        self.live = None
        self.animation_thread = None
        
    def _animation_loop(self):
        """Animation loop for indeterminate progress"""
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        frame_index = 0
        
        while self.is_running:
            frame = frames[frame_index % len(frames)]
            elapsed = time.time() - self.start_time if self.start_time else 0
            
            text = Text()
            text.append(f"{frame} ", style="bold blue")
            text.append(self.description, style="white")
            text.append(f" ({elapsed:.1f}s)", style="dim")
            
            panel = Panel(
                Align.center(text),
                border_style="blue",
                padding=(1, 2)
            )
            
            if self.live:
                self.live.update(panel)
            
            time.sleep(0.1)
            frame_index += 1
            
    def start(self):
        """Start animated progress"""
        self.start_time = time.time()
        self.is_running = True
        self.live = Live(console=console, refresh_per_second=10)
        self.live.start()
        
        self.animation_thread = threading.Thread(target=self._animation_loop)
        self.animation_thread.daemon = True
        self.animation_thread.start()
        
    def stop(self, final_message: str = "Complete!"):
        """Stop animated progress"""
        self.is_running = False
        
        if self.live:
            final_text = Text(f"✅ {final_message}", style="bold green")
            final_panel = Panel(
                Align.center(final_text),
                border_style="green",
                padding=(1, 2)
            )
            self.live.update(final_panel)
            time.sleep(1)  # Show completion briefly
            self.live.stop()
            
        if self.animation_thread:
            self.animation_thread.join(timeout=1)


class ProgressTracker:
    """High-level progress tracking for common operations"""
    
    @staticmethod
    def track_pdf_processing(file_path: str) -> ProgressIndicator:
        """Create progress indicator for PDF processing"""
        config = ProgressConfig(
            description=f"Processing PDF: {file_path}",
            show_spinner=True,
            show_time=True,
            total=100
        )
        return ProgressIndicator(config)
        
    @staticmethod
    def track_lesson_generation(grade: str, strand: str) -> ProgressIndicator:
        """Create progress indicator for lesson generation"""
        config = ProgressConfig(
            description=f"Generating {grade} {strand} lesson",
            show_spinner=True,
            show_time=True,
            total=100
        )
        return ProgressIndicator(config)
        
    @staticmethod
    def track_embeddings_generation(total_standards: int) -> ProgressIndicator:
        """Create progress indicator for embeddings generation"""
        config = ProgressConfig(
            description="Generating embeddings",
            show_percentage=True,
            show_time=True,
            show_speed=True,
            total=total_standards
        )
        return ProgressIndicator(config)
        
    @staticmethod
    def track_database_operation(operation: str) -> ProgressIndicator:
        """Create progress indicator for database operations"""
        config = ProgressConfig(
            description=f"Database: {operation}",
            show_spinner=True,
            show_time=True
        )
        return ProgressIndicator(config)
        
    @staticmethod
    def multi_step_lesson_generation() -> MultiStepProgress:
        """Create multi-step progress for lesson generation"""
        steps = [
            "Analyzing requirements",
            "Selecting standards",
            "Generating content",
            "Formatting lesson",
            "Finalizing output"
        ]
        return MultiStepProgress(steps)


# Convenience functions for common operations

def with_progress(description: str, total: Optional[int] = None):
        """Decorator to add progress to functions"""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                config = ProgressConfig(
                    description=description,
                    total=total,
                    show_percentage=total is not None,
                    show_time=True
                )
                progress = ProgressIndicator(config)
                
                try:
                    progress.start()
                    result = func(*args, **kwargs)
                    progress.finish()
                    return result
                except Exception as e:
                    progress.stop()
                    raise
                    
        return wrapper
        return decorator


def track_long_operation(operation_func: Callable, description: str, total: int = None) -> Any:
    """Track a long-running operation with progress"""
    progress = ProgressTracker()
    
    # Determine appropriate progress type
    if total:
        indicator = ProgressIndicator(ProgressConfig(
            description=description,
            total=total,
            show_percentage=True,
            show_time=True
        ))
    else:
        indicator = AnimatedProgress(description)
    
    try:
        if isinstance(indicator, AnimatedProgress):
            indicator.start()
            result = operation_func()
            indicator.stop("Operation completed")
        else:
            with indicator.progress_context(description, total):
                result = operation_func()
                
        return result
        
    except Exception as e:
        indicator.stop("Operation failed")
        raise


# Example usage patterns
if __name__ == "__main__":
    # Example 1: Simple progress
    def example_simple_progress():
        progress = ProgressIndicator()
        progress.start("Processing files", total=10)
        
        for i in range(10):
            time.sleep(0.5)  # Simulate work
            progress.update(1)
            
        progress.finish("All files processed!")
        
    # Example 2: Multi-step progress
    def example_multi_step():
        multi = MultiStepProgress([
            "Loading data",
            "Processing data", 
            "Saving results"
        ])
        
        multi.start_step(0)
        time.sleep(1)
        multi.finish_current_step()
        
        multi.start_step(1)
        for i in range(5):
            time.sleep(0.3)
            multi.update_current_step(20)
        multi.finish_current_step()
        
        multi.start_step(2)
        time.sleep(0.5)
        multi.finish_current_step()
        
    # Example 3: Animated progress
    def example_animated():
        animated = AnimatedProgress("Connecting to server...")
        animated.start()
        time.sleep(3)
        animated.stop("Connected successfully!")
        
    # Run examples
    console.print("[bold blue]Progress Indicator Examples[/bold blue]")
    
    console.print("\n1. Simple Progress:")
    example_simple_progress()
    
    console.print("\n2. Multi-step Progress:")
    example_multi_step()
    
    console.print("\n3. Animated Progress:")
    example_animated()