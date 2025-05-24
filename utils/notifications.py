"""
Windows notification system for Film Translator Generator
Provides native Windows notifications for processing completion
"""
import os
import sys
import time
import platform
from pathlib import Path
from typing import Optional

# Windows-specific imports
if platform.system() == "Windows":
    try:
        import win10toast
        from plyer import notification
        import winsound
        WINDOWS_NOTIFICATIONS_AVAILABLE = True
    except ImportError:
        WINDOWS_NOTIFICATIONS_AVAILABLE = False
        print("Windows notification libraries not available. Install with: pip install win10toast plyer")
else:
    WINDOWS_NOTIFICATIONS_AVAILABLE = False

class WindowsNotifier:
    """Handle Windows native notifications"""
    
    def __init__(self, app_name: str = "Film Translator Generator"):
        self.app_name = app_name
        self.icon_path = self._get_icon_path()
        
        if WINDOWS_NOTIFICATIONS_AVAILABLE:
            self.toaster = win10toast.ToastNotifier()
        else:
            self.toaster = None
    
    def _get_icon_path(self) -> str:
        """Get application icon path for notifications"""
        # Look for icon file in various locations
        possible_paths = [
            "assets/icon.ico",
            "icon.ico",
            "assets/logo.ico",
            "logo.ico"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        # Return None if no icon found (will use default)
        return None
    
    def show_completion_notification(
        self,
        title: str = "Processing Complete",
        message: str = "Video processing finished successfully",
        duration: int = 10,
        play_sound: bool = True,
        urgent: bool = False
    ):
        """Show a completion notification"""
        if not WINDOWS_NOTIFICATIONS_AVAILABLE:
            print(f"Notification: {title} - {message}")
            return
        
        try:
            # Use win10toast for rich notifications
            if self.toaster:
                self.toaster.show_toast(
                    title=f"{self.app_name} - {title}",
                    msg=message,
                    icon_path=self.icon_path,
                    duration=duration,
                    threaded=True
                )
            
            # Fallback to plyer
            else:
                notification.notify(
                    title=f"{self.app_name} - {title}",
                    message=message,
                    app_name=self.app_name,
                    timeout=duration
                )
            
            # Play notification sound
            if play_sound:
                self._play_notification_sound(urgent)
                
        except Exception as e:
            print(f"Error showing notification: {e}")
            # Fallback to console output
            print(f"Notification: {title} - {message}")
    
    def _play_notification_sound(self, urgent: bool = False):
        """Play system notification sound"""
        if platform.system() != "Windows":
            return
        
        try:
            if urgent:
                # Play critical sound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            else:
                # Play default notification sound
                winsound.MessageBeep(winsound.MB_ICONINFORMATION)
        except Exception as e:
            print(f"Error playing notification sound: {e}")
    
    def show_error_notification(
        self,
        title: str = "Processing Error",
        message: str = "An error occurred during processing",
        duration: int = 15
    ):
        """Show an error notification"""
        self.show_completion_notification(
            title=title,
            message=message,
            duration=duration,
            play_sound=True,
            urgent=True
        )
    
    def show_queue_complete_notification(
        self,
        processed_count: int,
        total_count: int,
        failed_count: int = 0,
        total_time: Optional[float] = None
    ):
        """Show notification when entire queue processing is complete"""
        success_count = processed_count - failed_count
        
        if failed_count == 0:
            title = "Queue Processing Complete"
            message = f"Successfully processed {success_count}/{total_count} videos"
            if total_time:
                message += f" in {self._format_time(total_time)}"
            urgent = False
        else:
            title = "Queue Processing Finished with Errors"
            message = f"Completed: {success_count}/{total_count} videos"
            if failed_count > 0:
                message += f" ({failed_count} failed)"
            urgent = True
        
        self.show_completion_notification(
            title=title,
            message=message,
            duration=15,
            urgent=urgent
        )
    
    def show_progress_notification(
        self,
        current_file: str,
        current_index: int,
        total_count: int,
        stage: str = "Processing"
    ):
        """Show progress notification for current file"""
        filename = os.path.basename(current_file)
        title = f"{stage} ({current_index}/{total_count})"
        message = f"Working on: {filename}"
        
        # Short duration for progress notifications
        self.show_completion_notification(
            title=title,
            message=message,
            duration=3,
            play_sound=False
        )
    
    def _format_time(self, seconds: float) -> str:
        """Format time duration for display"""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"


class NotificationManager:
    """Manage all notification types and preferences"""
    
    def __init__(self, app_name: str = "Film Translator Generator"):
        self.notifier = WindowsNotifier(app_name)
        self.settings = {
            'enabled': True,
            'sound_enabled': True,
            'progress_notifications': False,  # Disabled by default to avoid spam
            'error_notifications': True,
            'completion_notifications': True,
            'queue_notifications': True
        }
    
    def set_notification_preference(self, preference: str, enabled: bool):
        """Set notification preferences"""
        if preference in self.settings:
            self.settings[preference] = enabled
    
    def notify_processing_start(self, filename: str, index: int, total: int):
        """Notify when processing starts for a file"""
        if not self.settings['enabled'] or not self.settings['progress_notifications']:
            return
        
        self.notifier.show_progress_notification(
            current_file=filename,
            current_index=index,
            total_count=total,
            stage="Starting"
        )
    
    def notify_transcription_complete(self, filename: str):
        """Notify when transcription is complete"""
        if not self.settings['enabled'] or not self.settings['progress_notifications']:
            return
        
        self.notifier.show_completion_notification(
            title="Transcription Complete",
            message=f"Finished transcribing: {os.path.basename(filename)}",
            duration=5,
            play_sound=False
        )
    
    def notify_translation_complete(self, filename: str):
        """Notify when translation is complete"""
        if not self.settings['enabled'] or not self.settings['progress_notifications']:
            return
        
        self.notifier.show_completion_notification(
            title="Translation Complete",
            message=f"Finished translating: {os.path.basename(filename)}",
            duration=5,
            play_sound=False
        )
    
    def notify_file_complete(self, filename: str, output_path: str = None):
        """Notify when a single file processing is complete"""
        if not self.settings['enabled'] or not self.settings['completion_notifications']:
            return
        
        message = f"Successfully processed: {os.path.basename(filename)}"
        if output_path:
            message += f"\nSaved to: {os.path.basename(output_path)}"
        
        self.notifier.show_completion_notification(
            title="File Processing Complete",
            message=message,
            duration=8
        )
    
    def notify_processing_error(self, filename: str, error_message: str):
        """Notify when processing fails"""
        if not self.settings['enabled'] or not self.settings['error_notifications']:
            return
        
        self.notifier.show_error_notification(
            title="Processing Failed",
            message=f"Error processing {os.path.basename(filename)}: {error_message}"
        )
    
    def notify_queue_complete(self, stats: dict):
        """Notify when entire queue processing is complete"""
        if not self.settings['enabled'] or not self.settings['queue_notifications']:
            return
        
        self.notifier.show_queue_complete_notification(
            processed_count=stats.get('processed', 0),
            total_count=stats.get('total', 0),
            failed_count=stats.get('failed', 0),
            total_time=stats.get('total_time')
        )
    
    def test_notification(self):
        """Test notification system"""
        self.notifier.show_completion_notification(
            title="Notification Test",
            message="Windows notification system is working correctly!",
            duration=5
        )


# Global notification manager instance
notification_manager = NotificationManager()

# Convenience functions for easy import and use
def notify_processing_complete(filename: str, output_path: str = None):
    """Quick function to notify processing completion"""
    notification_manager.notify_file_complete(filename, output_path)

def notify_queue_complete(processed: int, total: int, failed: int = 0, total_time: float = None):
    """Quick function to notify queue completion"""
    stats = {
        'processed': processed,
        'total': total,
        'failed': failed,
        'total_time': total_time
    }
    notification_manager.notify_queue_complete(stats)

def notify_error(filename: str, error_message: str):
    """Quick function to notify errors"""
    notification_manager.notify_processing_error(filename, error_message)

def set_notifications_enabled(enabled: bool):
    """Quick function to enable/disable notifications"""
    notification_manager.set_notification_preference('enabled', enabled)

def test_notifications():
    """Quick function to test notification system"""
    notification_manager.test_notification() 