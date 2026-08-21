"""
Mustering Analytics Service
Advanced analytics and reporting for mustering system
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, extract
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.models.biotime_models import (
    MusteringEvent, MusteringLog, PersonnelEmployee,
    MusteringDrillSchedule,
)
# NOTE: this module used to import `MusteringTemplate`, which does not exist —
# the model is MusteringEventTemplate (table: mustering_template). It was never
# referenced anywhere in this file, so the only thing the bad name achieved was
# an ImportError that took down all four analytics endpoints. Import the real
# name here if template-based analytics are added later.
from app.models.zone import Zone

logger = logging.getLogger(__name__)

class MusteringAnalyticsService:
    """Advanced analytics service for mustering system"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_event_performance_analytics(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        zone_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive event performance analytics
        """
        try:
            # Set default date range (last 30 days)
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Base query
            query = self.db.query(MusteringEvent).filter(
                MusteringEvent.start_time >= start_date,
                MusteringEvent.start_time <= end_date,
                MusteringEvent.status == 1  # Completed events only
            )
            
            if zone_id:
                query = query.filter(MusteringEvent.zone_id == zone_id)
            
            events = query.all()
            
            if not events:
                return self._empty_analytics_response()
            
            # Calculate performance metrics
            total_events = len(events)
            
            # Event duration statistics
            durations = []
            for event in events:
                if event.end_time and event.start_time:
                    duration = (event.end_time - event.start_time).total_seconds() / 60
                    durations.append(duration)
            
            avg_duration = sum(durations) / len(durations) if durations else 0
            min_duration = min(durations) if durations else 0
            max_duration = max(durations) if durations else 0
            
            # Performance by event type
            event_type_stats = {}
            for event in events:
                event_type = event.event_type
                if event_type not in event_type_stats:
                    event_type_stats[event_type] = {
                        'count': 0,
                        'durations': []
                    }
                event_type_stats[event_type]['count'] += 1
                if event.end_time and event.start_time:
                    event_type_stats[event_type]['durations'].append(
                        (event.end_time - event.start_time).total_seconds() / 60
                    )
            
            # Calculate averages by event type
            for event_type in event_type_stats:
                durations = event_type_stats[event_type]['durations']
                if durations:
                    event_type_stats[event_type]['avg_duration'] = sum(durations) / len(durations)
                    event_type_stats[event_type]['min_duration'] = min(durations)
                    event_type_stats[event_type]['max_duration'] = max(durations)
                else:
                    event_type_stats[event_type]['avg_duration'] = 0
                    event_type_stats[event_type]['min_duration'] = 0
                    event_type_stats[event_type]['max_duration'] = 0
            
            # Personnel accountability metrics
            accountability_metrics = self._calculate_accountability_metrics(events)
            
            # Zone performance
            zone_performance = self._calculate_zone_performance(events)
            
            # Time-based analysis
            time_analysis = self._analyze_time_patterns(events)
            
            return {
                'summary': {
                    'total_events': total_events,
                    'date_range': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    },
                    'avg_duration_minutes': round(avg_duration, 2),
                    'min_duration_minutes': round(min_duration, 2),
                    'max_duration_minutes': round(max_duration, 2)
                },
                'event_type_performance': event_type_stats,
                'accountability_metrics': accountability_metrics,
                'zone_performance': zone_performance,
                'time_analysis': time_analysis,
                'compliance_score': self._calculate_compliance_score(events)
            }
            
        except Exception as e:
            logger.error(f"Error in get_event_performance_analytics: {e}")
            raise
    
    def get_personnel_mustering_history(
        self,
        emp_code: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get detailed personnel mustering history
        """
        try:
            # Set default date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=90)
            
            # Query mustering logs
            query = self.db.query(MusteringLog).join(
                MusteringEvent, MusteringLog.event_id == MusteringEvent.id
            ).filter(
                MusteringLog.check_time >= start_date,
                MusteringLog.check_time <= end_date
            )
            
            if emp_code:
                query = query.filter(MusteringLog.emp_code == emp_code)
            
            logs = query.order_by(desc(MusteringLog.check_time)).limit(limit).all()
            
            if not logs:
                return {
                    'personnel': [],
                    'statistics': {
                        'total_events': 0,
                        'safe_events': 0,
                        'injured_events': 0,
                        'avg_response_time': 0
                    }
                }
            
            # Process logs for analysis
            personnel_data = []
            for log in logs:
                personnel_data.append({
                    'event_id': log.event_id,
                    'event_type': log.event.event_type if log.event else None,
                    'check_time': log.check_time,
                    'status': log.status,
                    'device_sn': log.device_sn,
                    'device_alias': log.device_alias,
                    'zone_name': log.event.zone.name if log.event and log.event.zone else None,
                    'response_time': self._calculate_response_time(log)
                })
            
            # Calculate statistics
            total_events = len(set(log.event_id for log in logs))
            safe_events = len([log for log in logs if log.status == 1])
            injured_events = len([log for log in logs if log.status == 2])
            avg_response_time = sum(self._calculate_response_time(log) for log in logs) / len(logs)
            
            return {
                'personnel': personnel_data,
                'statistics': {
                    'total_events': total_events,
                    'safe_events': safe_events,
                    'injured_events': injured_events,
                    'avg_response_time': round(avg_response_time, 2),
                    'first_muster': logs[-1].check_time.isoformat() if logs else None,
                    'last_muster': logs[0].check_time.isoformat() if logs else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error in get_personnel_mustering_history: {e}")
            raise
    
    def get_zone_utilization_analytics(
        self,
        zone_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get zone utilization and capacity analytics
        """
        try:
            # Set default date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Query zones
            query = self.db.query(Zone)
            if zone_id:
                query = query.filter(Zone.id == zone_id)
            
            zones = query.all()
            
            if not zones:
                return self._empty_analytics_response()
            
            # Get events for each zone
            zone_analytics = {}
            total_expected = 0
            total_safe = 0
            
            for zone in zones:
                zone_events = self.db.query(MusteringEvent).filter(
                    and_(
                        MusteringEvent.zone_id == zone.id,
                        MusteringEvent.start_time >= start_date,
                        MusteringEvent.start_time <= end_date,
                        MusteringEvent.status == 1
                    )
                ).all()
                
                # Calculate zone metrics
                zone_total_expected = sum(event.total_expected or 0 for event in zone_events)
                zone_total_safe = sum(event.total_safe or 0 for event in zone_events)
                
                total_expected += zone_total_expected
                total_safe += zone_total_safe
                
                # Calculate utilization
                utilization_rate = 0
                if zone.max_capacity and zone.max_capacity > 0:
                    utilization_rate = (zone_total_safe / zone.max_capacity) * 100
                
                zone_analytics[zone.id] = {
                    'zone_name': zone.name,
                    'zone_type': zone.zone_type,
                    'capacity': zone.max_capacity,
                    'total_events': len(zone_events),
                    'total_expected': zone_total_expected,
                    'total_safe': zone_total_safe,
                    'utilization_rate': round(utilization_rate, 2),
                    'avg_muster_time': self._calculate_avg_muster_time(zone_events),
                    'peak_usage': self._calculate_peak_usage(zone_events)
                }
            
            # Calculate overall metrics
            overall_utilization = 0
            if zones:
                total_capacity = sum(zone.max_capacity for zone in zones if zone.max_capacity)
                if total_capacity > 0:
                    overall_utilization = (total_safe / total_capacity) * 100
            
            return {
                'summary': {
                    'total_zones': len(zones),
                    'total_capacity': sum(zone.max_capacity for zone in zones if zone.max_capacity),
                    'overall_utilization': round(overall_utilization, 2),
                    'total_expected': total_expected,
                    'total_safe': total_safe
                },
                'zone_details': zone_analytics,
                'recommendations': self._generate_utilization_recommendations(zone_analytics)
            }
            
        except Exception as e:
            logger.error(f"Error in get_zone_utilization_analytics: {e}")
            raise
    
    def get_drill_effectiveness_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get drill effectiveness analytics
        """
        try:
            # Set default date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=90)
            
            # Get drill events
            drill_events = self.db.query(MusteringEvent).filter(
                and_(
                    MusteringEvent.event_type == 1,  # Drill type
                    MusteringEvent.start_time >= start_date,
                    MusteringEvent.start_time <= end_date,
                    MusteringEvent.status == 1
                )
            ).all()
            
            # Get scheduled drills
            scheduled_drills = self.db.query(MusteringDrillSchedule).filter(
                MusteringDrillSchedule.scheduled_time >= start_date,
                MusteringDrillSchedule.scheduled_time <= end_date
            ).all()
            
            if not drill_events:
                return {
                    'summary': {
                        'total_drills': 0,
                        'scheduled_vs_executed': '0/0',
                        'avg_completion_time': 0,
                        'effectiveness_score': 0
                    },
                    'drill_details': [],
                    'recommendations': []
                }
            
            # Calculate effectiveness metrics
            total_drills = len(drill_events)
            completed_drills = len([e for e in drill_events if e.end_time])
            scheduled_count = len(scheduled_drills)
            
            # Calculate completion times
            completion_times = []
            for event in drill_events:
                if event.end_time and event.start_time:
                    completion_time = (event.end_time - event.start_time).total_seconds() / 60
                    completion_times.append(completion_time)
            
            avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
            
            # Calculate effectiveness score
            effectiveness_score = self._calculate_drill_effectiveness_score(drill_events)
            
            return {
                'summary': {
                    'total_drills': total_drills,
                    'scheduled_vs_executed': f'{completed_drills}/{scheduled_count}',
                    'avg_completion_time': round(avg_completion_time, 2),
                    'effectiveness_score': round(effectiveness_score, 2)
                },
                'drill_details': self._analyze_drill_details(drill_events),
                'trends': self._analyze_drill_trends(drill_events),
                'recommendations': self._generate_drill_recommendations(drill_events)
            }
            
        except Exception as e:
            logger.error(f"Error in get_drill_effectiveness_analytics: {e}")
            raise
    
    def get_realtime_metrics(
        self,
        event_id: int
    ) -> Dict[str, Any]:
        """
        Get real-time metrics for active event
        """
        try:
            event = self.db.query(MusteringEvent).filter(
                MusteringEvent.id == event_id
            ).first()
            
            if not event or event.status != 0:
                return {'status': 'no_active_event'}
            
            # Get current headcount
            headcount = self.db.query(MusteringLog).filter(
                MusteringLog.event_id == event_id
            ).all()
            
            total_safe = len([log for log in headcount if log.status == 1])
            total_missing = len([log for log in headcount if log.status == 0])
            total_injured = len([log for log in headcount if log.status == 2])
            total_expected = event.total_expected or 0
            
            # Calculate rates
            safe_rate = (total_safe / total_expected * 100) if total_expected > 0 else 0
            missing_rate = (total_missing / total_expected * 100) if total_expected > 0 else 0
            
            # Get recent activity (last 5 minutes)
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            recent_activity = self.db.query(MusteringLog).filter(
                and_(
                    MusteringLog.event_id == event_id,
                    MusteringLog.check_time >= five_minutes_ago
                )
            ).count()
            
            # Calculate muster rate (people per minute)
            event_duration = (datetime.utcnow() - event.start_time).total_seconds() / 60 if event.start_time else 0
            muster_rate = total_safe / event_duration if event_duration > 0 else 0
            
            return {
                'event_id': event_id,
                'zone_id': event.zone_id,
                'zone_name': event.zone.name if event.zone else 'Unknown',
                'event_type': event.event_type,
                'duration_minutes': round(event_duration, 2),
                'headcount': {
                    'total_expected': total_expected,
                    'total_safe': total_safe,
                    'total_missing': total_missing,
                    'total_injured': total_injured,
                    'completion_percentage': round((total_safe + total_injured) / total_expected * 100, 2) if total_expected > 0 else 0
                },
                'rates': {
                    'safe_rate': round(safe_rate, 2),
                    'missing_rate': round(missing_rate, 2),
                    'muster_rate_per_minute': round(muster_rate, 2)
                },
                'activity': {
                    'recent_scans': recent_activity,
                    'last_scan': headcount[-1].check_time.isoformat() if headcount else None
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in get_realtime_metrics: {e}")
            raise
    
    # Helper methods
    def _empty_analytics_response(self) -> Dict[str, Any]:
        """Return empty analytics response"""
        return {
            'summary': {
                'total_events': 0,
                'avg_duration_minutes': 0,
                'min_duration_minutes': 0,
                'max_duration_minutes': 0
            },
            'message': 'No data found for the specified criteria'
        }
    
    def _calculate_accountability_metrics(self, events: List) -> Dict[str, Any]:
        """Calculate personnel accountability metrics"""
        if not events:
            return {}
        
        # Calculate time to account for each person
        accountability_times = []
        for event in events:
            logs = self.db.query(MusteringLog).filter(
                MusteringLog.event_id == event.id
            ).all()
            
            for log in logs:
                if log.status in [1, 2]:  # Safe or Injured
                    time_to_account = (log.check_time - event.start_time).total_seconds() / 60
                    accountability_times.append(time_to_account)
        
        if accountability_times:
            return {
                'avg_time_to_account': sum(accountability_times) / len(accountability_times),
                'min_time_to_account': min(accountability_times),
                'max_time_to_account': max(accountability_times),
                'total_accounted_within_5min': len([t for t in accountability_times if t <= 5]),
                'total_accounted_within_10min': len([t for t in accountability_times if t <= 10])
            }
        else:
            return {
                'avg_time_to_account': 0,
                'min_time_to_account': 0,
                'max_time_to_account': 0,
                'total_accounted_within_5min': 0,
                'total_accounted_within_10min': 0
            }
    
    def _calculate_zone_performance(self, events: List) -> Dict[str, Any]:
        """Calculate zone performance metrics"""
        if not events:
            return {}
        
        zone_performance = {}
        for event in events:
            zone_id = event.zone_id
            if zone_id not in zone_performance:
                zone_performance[zone_id] = {
                    'zone_name': event.zone.name if event.zone else 'Unknown',
                    'total_events': 0,
                    'avg_completion_time': 0,
                    'total_safe': 0,
                    'total_expected': 0,
                    # Appended to below for every completed event; without it the
                    # first completed event raised KeyError and took the whole
                    # event-performance report down.
                    'completion_times': []
                }
            
            zone_performance[zone_id]['total_events'] += 1
            zone_performance[zone_id]['total_safe'] += event.total_safe or 0
            zone_performance[zone_id]['total_expected'] += event.total_expected or 0
            
            if event.end_time and event.start_time:
                duration = (event.end_time - event.start_time).total_seconds() / 60
                zone_performance[zone_id]['completion_times'].append(duration)
        
        # Calculate averages for each zone
        for zone_id in zone_performance:
            zone_data = zone_performance[zone_id]
            total_events = zone_data['total_events']
            completion_times = zone_data.get('completion_times', [])
            
            zone_data['avg_completion_time'] = sum(completion_times) / len(completion_times) if completion_times else 0
            zone_data['min_completion_time'] = min(completion_times) if completion_times else 0
            zone_data['max_completion_time'] = max(completion_times) if completion_times else 0
            
            # Calculate effectiveness
            if zone_data['total_expected'] > 0:
                zone_data['effectiveness'] = (zone_data['total_safe'] / zone_data['total_expected']) * 100
            else:
                zone_data['effectiveness'] = 0
        
        return zone_performance
    
    def _analyze_time_patterns(self, events: List) -> Dict[str, Any]:
        """Analyze time patterns in mustering events"""
        if not events:
            return {}
        
        # Extract hour of day and day of week
        hourly_data = {}
        weekly_data = {}
        
        for event in events:
            if event.start_time:
                hour = event.start_time.hour
                day_of_week = event.start_time.strftime('%A')
                
                hourly_data[hour] = hourly_data.get(hour, 0) + 1
                weekly_data[day_of_week] = weekly_data.get(day_of_week, 0) + 1
        
        # Find peak times
        peak_hour = max(hourly_data, key=hourly_data.get) if hourly_data else 0
        peak_day = max(weekly_data, key=weekly_data.get) if weekly_data else 0
        
        return {
            'hourly_distribution': hourly_data,
            'weekly_distribution': weekly_data,
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'busiest_times': {
                'hour': f"{peak_hour}:00 - {peak_hour + 1}:00",
                'day': peak_day
            }
        }
    
    def _calculate_compliance_score(self, events: List) -> float:
        """Calculate overall compliance score"""
        if not events:
            return 0.0
        
        scores = []
        for event in events:
            event_score = 0.0
            
            # Time score (40% weight) - lower is better
            if event.end_time and event.start_time:
                duration_minutes = (event.end_time - event.start_time).total_seconds() / 60
                if duration_minutes <= 5:
                    time_score = 100
                elif duration_minutes <= 10:
                    time_score = 80
                elif duration_minutes <= 15:
                    time_score = 60
                else:
                    time_score = max(0, 40 - (duration_minutes - 15))
            else:
                time_score = 0
            
            # Accountability score (40% weight)
            if event.total_expected and event.total_expected > 0:
                accountability_score = (event.total_safe / event.total_expected) * 100
            else:
                accountability_score = 0
            
            # Type score (20% weight)
            type_score = 100  # All event types get full score
            
            event_score = (time_score * 0.4) + (accountability_score * 0.4) + (type_score * 0.2)
            scores.append(event_score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_response_time(self, log) -> float:
        """Calculate response time for a person"""
        if not log or not log.event or not log.event.start_time:
            return 0.0
        
        return (log.check_time - log.event.start_time).total_seconds() / 60
    
    def _calculate_avg_muster_time(self, events: List) -> float:
        """Calculate average muster time for events"""
        if not events:
            return 0.0
        
        total_time = 0
        event_count = 0
        
        for event in events:
            if event.end_time and event.start_time:
                total_time += (event.end_time - event.start_time).total_seconds()
                event_count += 1
        
        return (total_time / event_count / 60) if event_count > 0 else 0.0
    
    def _calculate_peak_usage(self, events: List) -> Dict[str, Any]:
        """Calculate peak usage for zones"""
        if not events:
            return {}
        
        zone_peak_usage = {}
        for event in events:
            zone_id = event.zone_id
            if zone_id not in zone_peak_usage:
                zone_peak_usage[zone_id] = {
                    'zone_name': event.zone.name if event.zone else 'Unknown',
                    'peak_safe': 0,
                    'peak_time': None,
                    'peak_date': None
                }
            
            safe_count = event.total_safe or 0
            if safe_count > zone_peak_usage[zone_id]['peak_safe']:
                zone_peak_usage[zone_id]['peak_safe'] = safe_count
                zone_peak_usage[zone_id]['peak_time'] = event.start_time
                zone_peak_usage[zone_id]['peak_date'] = event.start_time.date()
        
        return zone_peak_usage
    
    def _analyze_drill_details(self, events: List) -> List[Dict[str, Any]]:
        """Analyze individual drill details"""
        details = []
        
        for event in events:
            logs = self.db.query(MusteringLog).filter(
                MusteringLog.event_id == event.id
            ).all()
            
            detail = {
                'event_id': event.id,
                'zone_name': event.zone.name if event.zone else 'Unknown',
                'start_time': event.start_time,
                'end_time': event.end_time,
                'duration_minutes': round((event.end_time - event.start_time).total_seconds() / 60, 2) if event.end_time else None,
                'total_expected': event.total_expected,
                'total_safe': event.total_safe,
                'completion_rate': round((event.total_safe / event.total_expected) * 100, 2) if event.total_expected else 0,
                'participant_count': len(logs),
                'unique_participants': len(set(log.emp_code for log in logs))
            }
            
            # Add participant details
            participants = []
            for log in logs:
                participants.append({
                    'emp_code': log.emp_code,
                    'emp_name': log.emp_name,
                    'status': log.status,
                    'check_time': log.check_time,
                    'response_time': round((log.check_time - event.start_time).total_seconds() / 60, 2),
                    'device_sn': log.device_sn
                })
            
            detail['participants'] = participants
            details.append(detail)
        
        return details
    
    def _analyze_drill_trends(self, events: List) -> Dict[str, Any]:
        """Analyze drill trends over time"""
        if not events:
            return {}
        
        # Monthly drill counts
        monthly_counts = {}
        for event in events:
            month = event.start_time.strftime('%Y-%m')
            monthly_counts[month] = monthly_counts.get(month, 0) + 1
        
        # Calculate improvement trends
        months = sorted(monthly_counts.keys())
        if len(months) < 2:
            return {'monthly_counts': monthly_counts}
        
        trends = []
        for i in range(1, len(months)):
            current_month = months[i]
            previous_month = months[i-1]
            
            if previous_month in monthly_counts:
                improvement = ((monthly_counts[current_month] - monthly_counts[previous_month]) / monthly_counts[previous_month]) * 100
                trends.append({
                    'month': current_month,
                    'count': monthly_counts[current_month],
                    'previous_count': monthly_counts[previous_month],
                    'improvement_percentage': round(improvement, 2)
                })
        
        return {
            'monthly_counts': monthly_counts,
            'trends': trends,
            'average_per_month': sum(monthly_counts.values()) / len(monthly_counts)
        }
    
    def _generate_utilization_recommendations(self, zone_analytics: Dict) -> List[str]:
        """Generate utilization recommendations"""
        recommendations = []
        
        for zone_id, zone_data in zone_analytics.items():
            if zone_data['utilization_rate'] < 50:
                recommendations.append(
                    f"Zone '{zone_data['zone_name']}' has low utilization ({zone_data['utilization_rate']}%). "
                    f"Consider reviewing zone capacity or muster point accessibility."
                )
            elif zone_data['utilization_rate'] > 90:
                recommendations.append(
                    f"Zone '{zone_data['zone_name']}' has very high utilization ({zone_data['utilization_rate']}%). "
                    f"Consider increasing zone capacity or adding additional muster points."
                )
            elif zone_data['avg_muster_time'] > 15:
                recommendations.append(
                    f"Zone '{zone_data['zone_name']}' has slow average muster time ({zone_data['avg_muster_time']} minutes). "
                    f"Review evacuation procedures and zone layout."
                )
        
        return recommendations
    
    def _generate_drill_recommendations(self, events: List) -> List[str]:
        """Generate drill recommendations"""
        recommendations = []
        
        if not events:
            return ["No drill data available for analysis"]
        
        avg_completion_time = sum(
            (event.end_time - event.start_time).total_seconds() / 60 
            for event in events if event.end_time
        ) / len(events) if events else 0
        
        if avg_completion_time > 20:
            recommendations.append(
                f"Average drill completion time is {avg_completion_time:.1f} minutes. "
                f"Consider more frequent drills or improving evacuation procedures."
            )
        
        completion_rate = sum(
            (event.total_safe / event.total_expected) * 100 
            for event in events if event.total_expected
        ) / len(events) if events else 0
        
        if completion_rate < 80:
            recommendations.append(
                f"Average drill completion rate is {completion_rate:.1f}%. "
                f"Focus on improving personnel awareness and evacuation procedures."
            )
        
        # Check for patterns in failed drills
        failed_drills = [e for e in events if e.total_safe < (e.total_expected * 0.8)]
        if len(failed_drills) > len(events) * 0.3:
            recommendations.append(
                f"Multiple drills showing low completion rates. "
                f"Consider additional training and procedure review."
            )
        
        return recommendations
    
    def _calculate_drill_effectiveness_score(self, events: List) -> float:
        """Calculate drill effectiveness score"""
        if not events:
            return 0.0
        
        scores = []
        for event in events:
            event_score = 0.0
            
            # Time score (50%)
            if event.end_time and event.start_time:
                duration_minutes = (event.end_time - event.start_time).total_seconds() / 60
                if duration_minutes <= 5:
                    time_score = 100
                elif duration_minutes <= 10:
                    time_score = 90
                elif duration_minutes <= 15:
                    time_score = 80
                elif duration_minutes <= 20:
                    time_score = 70
                else:
                    time_score = 50
            else:
                time_score = 0
            
            # Completion score (30%)
            if event.total_expected and event.total_expected > 0:
                completion_rate = (event.total_safe / event.total_expected)
                if completion_rate >= 0.95:
                    completion_score = 100
                elif completion_rate >= 0.90:
                    completion_score = 90
                elif completion_rate >= 0.80:
                    completion_score = 80
                elif completion_rate >= 0.70:
                    completion_score = 70
                else:
                    completion_score = 50
            else:
                completion_score = 0
            
            # Participation score (20%)
            total_logs = self.db.query(MusteringLog).filter(
                MusteringLog.event_id == event.id
            ).count()
            expected_logs = event.total_expected or 1
            participation_rate = min((total_logs / expected_logs) * 100, 100)
            
            if participation_rate >= 95:
                participation_score = 100
            elif participation_rate >= 90:
                participation_score = 90
            elif participation_rate >= 80:
                    participation_score = 80
            elif participation_rate >= 70:
                    participation_score = 70
            else:
                    participation_score = 50
            
            event_score = (time_score * 0.5) + (completion_score * 0.3) + (participation_score * 0.2)
            scores.append(event_score)
        
        return sum(scores) / len(scores) if scores else 0.0
