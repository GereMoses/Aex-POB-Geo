"""
Enhanced Mustering Dashboard Service
Advanced dashboard features with real-time monitoring, predictive analytics, and performance metrics
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, extract
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import json

from app.models.biotime_models import (
    MusteringEvent, MusteringLog, PersonnelEmployee
)
from app.models.zone import Zone

logger = logging.getLogger(__name__)

class MusteringDashboardService:
    """Enhanced mustering dashboard service with advanced features"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_realtime_dashboard_data(self, event_id: int) -> Dict[str, Any]:
        """
        Get comprehensive real-time dashboard data for active event
        """
        try:
            # Get event and zone information
            event = self.db.query(MusteringEvent).filter(MusteringEvent.id == event_id).first()
            if not event or event.status != 0:
                return {'error': 'Event not found or not active'}
            
            zone = self.db.query(Zone).filter(Zone.id == event.zone_id).first()
            
            # Get real-time headcount
            headcount_query = self.db.query(
                func.count(MusteringLog.id).label('total'),
                func.sum(func.case([(MusteringLog.status == 1, 1)], [(MusteringLog.status == 0, 1)]).label('safe')),
                func.sum(func.case([(MusteringLog.status == 2, 1)], [(MusteringLog.status == 2, 1)]).label('injured'))
            ).filter(MusteringLog.event_id == event_id)
            
            headcount_result = headcount_query.first()
            
            # Get recent activity (last 5 minutes)
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            recent_activity = self.db.query(MusteringLog).filter(
                and_(
                    MusteringLog.event_id == event_id,
                    MusteringLog.check_time >= five_minutes_ago
                )
            ).order_by(desc(MusteringLog.check_time)).limit(10).all()
            
            # Calculate performance metrics
            event_duration = (datetime.utcnow() - event.start_time).total_seconds() / 60 if event.start_time else 0
            completion_rate = (headcount_result.safe / event.total_expected * 100) if event.total_expected > 0 else 0
            
            # Get zone capacity and utilization
            zone_utilization = 0
            if zone and zone.max_capacity:
                zone_utilization = (headcount_result.safe / zone.max_capacity) * 100
            
            # Predictive analytics
            predicted_completion_time = self._predict_completion_time(event_id, headcount_result.safe, event.total_expected)
            risk_level = self._calculate_risk_level(event, headcount_result)
            
            return {
                'event_info': {
                    'event_id': event.id,
                    'event_type': event.event_type,
                    'zone_name': zone.name if zone else 'Unknown',
                    'start_time': event.start_time.isoformat(),
                    'duration_minutes': round(event_duration, 2),
                    'initiated_by': event.initiated_by,
                    'status': event.status
                },
                'realtime_headcount': {
                    'total_expected': event.total_expected,
                    'total_safe': headcount_result.safe,
                    'total_missing': headcount_result.total,
                    'total_injured': headcount_result.injured,
                    'completion_rate': round(completion_rate, 2),
                    'accounted_percentage': round(((headcount_result.safe + headcount_result.injured) / event.total_expected) * 100, 2)
                },
                'zone_utilization': {
                    'capacity': zone.max_capacity if zone else 0,
                    'utilization_rate': round(zone_utilization, 2),
                    'utilization_level': self._get_utilization_level(zone_utilization)
                },
                'performance_metrics': {
                    'avg_response_time': self._calculate_avg_response_time(event_id),
                    'muster_rate_per_minute': round(headcount_result.safe / event_duration, 2) if event_duration > 0 else 0,
                    'completion_efficiency': self._calculate_completion_efficiency(completion_rate, event_duration),
                    'predicted_completion_time': predicted_completion_time
                },
                'risk_assessment': {
                    'risk_level': risk_level,
                    'risk_factors': self._identify_risk_factors(event, headcount_result),
                    'recommendations': self._generate_recommendations(risk_level, event, headcount_result)
                },
                'recent_activity': [
                    {
                        'emp_code': log.emp_code,
                        'emp_name': log.emp_name,
                        'check_time': log.check_time.isoformat(),
                        'status': log.status,
                        'device_sn': log.device_sn,
                        'response_time_seconds': self._calculate_response_time(log, event)
                    } for log in recent_activity
                ],
                'alerts': self._get_active_alerts(event_id),
                'last_update': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time dashboard data: {e}")
            return {'error': str(e)}
    
    def get_predictive_analytics(self, zone_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """
        Get predictive analytics for mustering performance
        """
        try:
            # Set date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get historical events for analysis
            events_query = self.db.query(MusteringEvent).filter(
                and_(
                    MusteringEvent.start_time >= start_date,
                    MusteringEvent.start_time <= end_date,
                    MusteringEvent.status == 1  # Completed events
                )
            )
            
            if zone_id:
                events_query = events_query.filter(MusteringEvent.zone_id == zone_id)
            
            events = events_query.order_by(desc(MusteringEvent.start_time)).limit(100).all()
            
            if not events:
                return {
                    'message': f'No historical data found for the specified criteria',
                    'analytics': {}
                }
            
            # Calculate predictive metrics
            analytics = self._calculate_predictive_metrics(events)
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting predictive analytics: {e}")
            return {'error': str(e)}
    
    def get_performance_trends(self, metric_type: str, period_days: int = 90) -> Dict[str, Any]:
        """
        Get performance trends for mustering system
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Get events for trend analysis
            events = self.db.query(MusteringEvent).filter(
                and_(
                    MusteringEvent.start_time >= start_date,
                    MusteringEvent.start_time <= end_date,
                    MusteringEvent.status == 1,
                )
            ).order_by(desc(MusteringEvent.start_time)).all()
            
            if not events:
                return {
                    'message': 'No events found for trend analysis',
                    'trends': {}
                }
            
            # Calculate trends based on metric type
            trends = self._calculate_performance_trends(events, metric_type)
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': period_days
                },
                'metric_type': metric_type,
                'trends': trends
            }
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            return {'error': str(e)}
    
    def get_zone_performance_comparison(self, zone_ids: List[int]) -> Dict[str, Any]:
        """
        Compare performance across multiple zones
        """
        try:
            if not zone_ids:
                return {'error': 'No zones specified for comparison'}
            
            # Get performance data for each zone
            zone_performance = {}
            
            for zone_id in zone_ids:
                zone = self.db.query(Zone).filter(Zone.id == zone_id).first()
                if not zone:
                    continue
                
                # Get recent events for this zone
                recent_events = self.db.query(MusteringEvent).filter(
                    and_(
                        MusteringEvent.zone_id == zone_id,
                        MusteringEvent.start_time >= datetime.utcnow() - timedelta(days=30)
                    )
                ).order_by(desc(MusteringEvent.start_time)).limit(10).all()
                
                # Calculate zone metrics
                zone_metrics = self._calculate_zone_metrics(zone, recent_events)
                zone_performance[zone_id] = {
                    'zone_info': {
                        'id': zone.id,
                        'name': zone.name,
                        'capacity': zone.max_capacity
                    },
                    'metrics': zone_metrics,
                    'recent_events': len(recent_events)
                }
            
            # Calculate comparative analysis
            comparison = self._calculate_zone_comparison(zone_performance)
            
            return {
                'zone_performance': zone_performance,
                'comparison': comparison,
                'analysis_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting zone performance comparison: {e}")
            return {'error': str(e)}
    
    def get_kpi_dashboard(self, time_period: str = 'month') -> Dict[str, Any]:
        """
        Get comprehensive KPI dashboard for management
        """
        try:
            # Set date range based on time period
            end_date = datetime.utcnow()
            if time_period == 'week':
                start_date = end_date - timedelta(weeks=1)
            elif time_period == 'month':
                start_date = end_date - timedelta(days=30)
            elif time_period == 'quarter':
                start_date = end_date - timedelta(days=90)
            elif time_period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)  # Default to month
            
            # Get events for KPI calculation
            events = self.db.query(MusteringEvent).filter(
                and_(
                    MusteringEvent.start_time >= start_date,
                    MusteringEvent.start_time <= end_date
                )
            ).all()
            
            if not events:
                return {
                    'message': 'No events found for KPI calculation',
                    'kpi': {}
                }
            
            # Calculate KPIs
            kpi_data = self._calculate_comprehensive_kpis(events)
            
            return {
                'period': {
                    'type': time_period,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'kpi': kpi_data
            }
            
        except Exception as e:
            logger.error(f"Error getting KPI dashboard: {e}")
            return {'error': str(e)}
    
    # Helper methods for advanced analytics
    def _calculate_avg_response_time(self, event_id: int) -> float:
        """Calculate average response time for an event"""
        try:
            logs = self.db.query(MusteringLog).filter(MusteringLog.event_id == event_id).all()
            event = self.db.query(MusteringEvent).filter(MusteringEvent.id == event_id).first()
            
            if not event or not logs:
                return 0.0
            
            response_times = []
            for log in logs:
                if log.check_time and event.start_time:
                    response_time = (log.check_time - event.start_time).total_seconds()
                    response_times.append(response_time)
            
            return sum(response_times) / len(response_times) if response_times else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating average response time: {e}")
            return 0.0
    
    def _calculate_completion_efficiency(self, completion_rate: float, duration_minutes: float) -> float:
        """Calculate completion efficiency score"""
        if duration_minutes <= 0:
            return 0.0
        
        # Efficiency based on completion rate and time
        time_efficiency = max(0, 100 - (duration_minutes / 10 * 100))  # Penalty for taking too long
        rate_efficiency = completion_rate
        
        # Weighted score (70% rate, 30% time)
        efficiency_score = (rate_efficiency * 0.7) + (time_efficiency * 0.3)
        
        return round(efficiency_score, 2)
    
    def _predict_completion_time(self, event_id: int, current_safe: int, total_expected: int) -> str:
        """Predict completion time based on current progress"""
        try:
            if current_safe == 0 or total_expected == 0:
                return "Cannot predict - no progress yet"
            
            # Calculate current rate
            current_rate = current_safe / total_expected
            remaining = total_expected - current_safe
            
            # Get historical average completion time for similar events
            avg_completion_time = self._get_historical_avg_completion(event_id)
            
            # Predict based on current rate and historical average
            if avg_completion_time > 0:
                # Weighted prediction (70% current rate, 30% historical average)
                predicted_minutes = (remaining / current_rate * avg_completion_time * 0.7) + (avg_completion_time * 0.3)
            else:
                predicted_minutes = remaining / max(current_rate, 0.1) * 10  # Minimum 10% per minute
            
            predicted_time = datetime.utcnow() + timedelta(minutes=predicted_minutes)
            
            return predicted_time.isoformat()
            
        except Exception as e:
            logger.error(f"Error predicting completion time: {e}")
            return datetime.utcnow().isoformat()
    
    def _get_historical_avg_completion(self, event_id: int) -> float:
        """Get historical average completion time for similar events"""
        try:
            event = self.db.query(MusteringEvent).filter(MusteringEvent.id == event_id).first()
            if not event:
                return 0.0
            
            # Get similar completed events
            similar_events = self.db.query(MusteringEvent).filter(
                and_(
                    MusteringEvent.zone_id == event.zone_id,
                    MusteringEvent.event_type == event.event_type,
                    MusteringEvent.status == 1
                )
            ).order_by(desc(MusteringEvent.start_time)).limit(10).all()
            
            if not similar_events:
                return 0.0
            
            # Calculate average completion time
            completion_times = []
            for similar_event in similar_events:
                if similar_event.end_time and similar_event.start_time:
                    duration = (similar_event.end_time - similar_event.start_time).total_seconds() / 60
                    completion_times.append(duration)
            
            return sum(completion_times) / len(completion_times) if completion_times else 0.0
            
        except Exception as e:
            logger.error(f"Error getting historical average completion: {e}")
            return 0.0
    
    def _calculate_risk_level(self, event, headcount) -> str:
        """Calculate risk level based on event and headcount"""
        try:
            risk_score = 0.0
            
            # Event type risk
            event_type_risk = {
                0: 0.2,  # Real
                1: 0.1,  # Drill
                2: 0.8,  # Fire
                3: 0.6,  # Gas
                4: 0.9   # Man Down
            }
            risk_score += event_type_risk.get(event.event_type, 0.0)
            
            # Completion rate risk
            completion_rate = (headcount.safe / event.total_expected) if event.total_expected > 0 else 0
            if completion_rate < 0.5:
                risk_score += 0.3  # Very high risk
            elif completion_rate < 0.7:
                risk_score += 0.2  # High risk
            elif completion_rate < 0.9:
                risk_score += 0.1  # Medium risk
            # Low risk (>= 90%)
            
            # Duration risk
            duration = (datetime.utcnow() - event.start_time).total_seconds() / 60 if event.start_time else 0
            if duration > 30:
                risk_score += 0.2  # High risk
            elif duration > 15:
                risk_score += 0.1  # Medium risk
            # Low risk (<= 15 minutes)
            
            # Determine risk level
            if risk_score >= 0.8:
                return 'critical'
            elif risk_score >= 0.6:
                return 'high'
            elif risk_score >= 0.3:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"Error calculating risk level: {e}")
            return 'low'
    
    def _identify_risk_factors(self, event, headcount) -> List[str]:
        """Identify specific risk factors"""
        risk_factors = []
        
        try:
            # Check for high missing rate
            completion_rate = (headcount.safe / event.total_expected) if event.total_expected > 0 else 0
            if completion_rate < 0.5:
                risk_factors.append('Low completion rate')
            
            # Check for long duration
            duration = (datetime.utcnow() - event.start_time).total_seconds() / 60 if event.start_time else 0
            if duration > 20:
                risk_factors.append('Extended duration')
            
            # Check for event type
            high_risk_types = [2, 3, 4]  # Fire, Gas, Man Down
            if event.event_type in high_risk_types:
                risk_factors.append('High-risk event type')
            
            # Check for time of day
            current_hour = datetime.utcnow().hour
            if current_hour < 6 or current_hour > 22:
                risk_factors.append('Off-hours mustering')
            
        except Exception as e:
            logger.error(f"Error identifying risk factors: {e}")
            return []
    
    def _generate_recommendations(self, risk_level: str, event, headcount) -> List[str]:
        """Generate recommendations based on risk assessment"""
        recommendations = []
        
        try:
            if risk_level == 'critical':
                recommendations.extend([
                    'Immediate action required',
                    'Notify emergency services',
                    'Initiate full evacuation protocol',
                    'Consider declaring emergency'
                ])
            elif risk_level == 'high':
                recommendations.extend([
                    'Accelerate mustering efforts',
                    'Increase notification frequency',
                    'Consider additional muster points',
                    'Review evacuation procedures'
                ])
            elif risk_level == 'medium':
                recommendations.extend([
                    'Monitor progress closely',
                    'Prepare contingency plans',
                    'Increase supervisor presence',
                    'Review communication protocols'
                ])
            elif risk_level == 'low':
                recommendations.extend([
                    'Maintain current pace',
                    'Continue regular monitoring',
                    'Document lessons learned',
                    'Optimize processes for next time'
                ])
            
            # Add specific recommendations based on factors
            completion_rate = (headcount.safe / event.total_expected) if event.total_expected > 0 else 0
            if completion_rate < 0.5:
                recommendations.append('Conduct post-muster debrief')
            
            duration = (datetime.utcnow() - event.start_time).total_seconds() / 60 if event.start_time else 0
            if duration > 15:
                recommendations.append('Review time management procedures')
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _get_utilization_level(self, utilization_rate: float) -> str:
        """Get utilization level description"""
        if utilization_rate >= 90:
            return 'At capacity'
        elif utilization_rate >= 75:
            return 'High utilization'
        elif utilization_rate >= 50:
            return 'Moderate utilization'
        elif utilization_rate >= 25:
            return 'Low utilization'
        else:
            return 'Very low utilization'
    
    def _calculate_zone_metrics(self, zone, recent_events) -> Dict[str, Any]:
        """Calculate performance metrics for a zone"""
        try:
            if not recent_events:
                return {
                    'total_events': 0,
                    'avg_duration': 0,
                    'completion_rate': 0,
                    'utilization_rate': 0
                }
            
            # Calculate metrics
            total_events = len(recent_events)
            durations = []
            completion_rates = []
            
            for event in recent_events:
                if event.end_time and event.start_time:
                    duration = (event.end_time - event.start_time).total_seconds() / 60
                    durations.append(duration)
                    
                    if event.total_expected and event.total_expected > 0:
                        completion_rate = (event.total_safe / event.total_expected) * 100
                        completion_rates.append(completion_rate)
            
            avg_duration = sum(durations) / len(durations) if durations else 0
            avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0
            
            utilization_rate = 0
            if zone and zone.max_capacity and zone.max_capacity > 0:
                total_safe = sum(event.total_safe for event in recent_events if event.total_safe)
                utilization_rate = (total_safe / (zone.max_capacity * len(recent_events))) * 100
            
            return {
                'total_events': total_events,
                'avg_duration': round(avg_duration, 2),
                'completion_rate': round(avg_completion_rate, 2),
                'utilization_rate': round(utilization_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating zone metrics: {e}")
            return {}
    
    def _calculate_zone_comparison(self, zone_performance) -> Dict[str, Any]:
        """Calculate comparative analysis between zones"""
        try:
            zones = list(zone_performance.values())
            
            if len(zones) < 2:
                return {'message': 'Need at least 2 zones for comparison'}
            
            # Find best and worst performing zones
            completion_rates = [zone['metrics']['completion_rate'] for zone in zones if zone.get('metrics')]
            utilization_rates = [zone['metrics']['utilization_rate'] for zone in zones if zone.get('metrics')]
            
            best_completion = max(completion_rates) if completion_rates else 0
            worst_completion = min(completion_rates) if completion_rates else 0
            best_utilization = max(utilization_rates) if utilization_rates else 0
            worst_utilization = min(utilization_rates) if utilization_rates else 0
            
            best_zone = None
            worst_zone = None
            
            for zone_id, zone_data in zone_performance.items():
                if zone_data.get('metrics', {}).get('completion_rate') == best_completion:
                    best_zone = zone_id
                elif zone_data.get('metrics', {}).get('completion_rate') == worst_completion:
                    worst_zone = zone_id
            
            return {
                'best_performing_zone': best_zone,
                'worst_performing_zone': worst_zone,
                'performance_spread': best_completion - worst_completion if worst_completion != 0 else 0,
                'utilization_spread': best_utilization - worst_utilization if worst_utilization != 0 else 0,
                'recommendations': [
                    'Share best practices from top-performing zone',
                    'Provide additional training to underperforming zones',
                    'Consider resource reallocation'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error calculating zone comparison: {e}")
            return {}
    
    def _calculate_predictive_metrics(self, events) -> Dict[str, Any]:
        """Calculate predictive analytics from historical data"""
        try:
            if not events:
                return {}
            
            # Event type distribution
            event_types = {}
            for event in events:
                event_type = event.event_type
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # Duration trends
            durations = []
            for event in events:
                if event.end_time and event.start_time:
                    duration = (event.end_time - event.start_time).total_seconds() / 60
                    durations.append(duration)
            
            # Completion rate trends
            completion_rates = []
            for event in events:
                if event.total_expected and event.total_expected > 0:
                    completion_rate = (event.total_safe / event.total_expected) * 100
                    completion_rates.append(completion_rate)
            
            return {
                'event_type_distribution': event_types,
                'duration_statistics': {
                    'avg': round(sum(durations) / len(durations), 2) if durations else 0,
                    'min': round(min(durations), 2) if durations else 0,
                    'max': round(max(durations), 2) if durations else 0,
                    'trend': 'improving' if len(durations) >= 3 and self._is_improving_trend(durations[-3:]) else 'stable'
                },
                'completion_rate_statistics': {
                    'avg': round(sum(completion_rates) / len(completion_rates), 2) if completion_rates else 0,
                    'min': round(min(completion_rates), 2) if completion_rates else 0,
                    'max': round(max(completion_rates), 2) if completion_rates else 0,
                    'trend': 'improving' if len(completion_rates) >= 3 and self._is_improving_trend(completion_rates[-3:]) else 'stable'
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating predictive metrics: {e}")
            return {}
    
    def _is_improving_trend(self, recent_values: List[float]) -> bool:
        """Check if recent values show improvement trend"""
        if len(recent_values) < 3:
            return False
        
        # Check if last 3 values are consistently increasing
        return all(recent_values[i] < recent_values[i+1] for i in range(len(recent_values)-1))
    
    def _calculate_comprehensive_kpis(self, events) -> Dict[str, Any]:
        """Calculate comprehensive KPIs for mustering system"""
        try:
            if not events:
                return {}
            
            total_events = len(events)
            completed_events = len([e for e in events if e.status == 1])
            
            # Duration metrics
            durations = []
            for event in events:
                if event.end_time and event.start_time:
                    duration = (event.end_time - event.start_time).total_seconds() / 60
                    durations.append(duration)
            
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Completion rate metrics
            completion_rates = []
            total_expecteds = []
            
            for event in events:
                if event.total_expected:
                    total_expecteds.append(event.total_expected)
                    if event.total_safe and event.total_expected > 0:
                        completion_rate = (event.total_safe / event.total_expected) * 100
                        completion_rates.append(completion_rate)
            
            avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0
            
            # Event type analysis
            event_type_counts = {}
            for event in events:
                event_type = event.event_type
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            
            # Zone performance
            zone_performance = {}
            for event in events:
                zone_id = event.zone_id
                if zone_id not in zone_performance:
                    zone_performance[zone_id] = {
                        'events': 0,
                        'total_safe': 0,
                        'total_expected': 0
                    }
                
                zone_performance[zone_id]['events'] += 1
                zone_performance[zone_id]['total_safe'] += event.total_safe or 0
                zone_performance[zone_id]['total_expected'] = event.total_expected
            
            # Calculate zone averages
            for zone_id in zone_performance:
                zone_data = zone_performance[zone_id]
                zone = self.db.query(Zone).filter(Zone.id == zone_id).first()
                if zone_data['events'] > 0:
                    zone_total_expecteds = [
                        total_expecteds[i]
                        for i, event in enumerate(events)
                        if event.zone_id == zone_id
                    ]
                    zone_data['avg_completion_rate'] = (
                        sum(
                            completion_rates[i]
                            for i, event in enumerate(events)
                            if event.zone_id == zone_id and event.total_expected and event.total_safe
                        ) / sum(zone_total_expecteds)
                    ) if any(zone_total_expecteds) else 0
                
                zone_data['avg_utilization'] = 0
                if zone_data['events'] > 0 and zone.max_capacity:
                    total_safe = sum(
                        zone_data['total_safe'] 
                        for i, event in enumerate(events) 
                        if event.zone_id == zone_id
                    )
                    zone_data['avg_utilization'] = (total_safe / (zone.max_capacity * zone_data['events'])) * 100
            
            # Find best and worst zones
            zone_avg_completion_rates = {
                zone_id: zone_data['avg_completion_rate'] 
                for zone_id, zone_data in zone_performance.items()
            }
            
            best_zone_id = max(zone_avg_completion_rates, key=zone_avg_completion_rates.get) if zone_avg_completion_rates else 0
            worst_zone_id = min(zone_avg_completion_rates, key=zone_avg_completion_rates.get) if zone_avg_completion_rates else 0
            
            return {
                'total_events': total_events,
                'completed_events': completed_events,
                'completion_rate': round(avg_completion_rate, 2),
                'avg_duration_minutes': round(avg_duration, 2),
                'event_type_distribution': event_type_counts,
                'zone_performance': zone_performance,
                'best_performing_zone': best_zone_id,
                'worst_performing_zone': worst_zone_id,
                'performance_gap': round(zone_avg_completion_rates.get(best_zone_id, 0) - zone_avg_completion_rates.get(worst_zone_id, 0), 2),
                'trends': {
                    'completion_rate_trend': 'improving' if self._is_improving_trend(
                        [completion_rates[i] for i in range(len(completion_rates)-3)]
                    ) else 'stable',
                    'duration_trend': 'improving' if self._is_improving_trend(durations[-3:]) else 'stable',
                },
            }
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive KPIs: {e}")
            return {}
    
    def _get_active_alerts(self, event_id: int) -> List[Dict[str, Any]]:
        """Get active alerts for an event"""
        try:
            # This would query an alerts table in a real implementation
            # For now, return mock alerts based on event conditions
            
            event = self.db.query(MusteringEvent).filter(MusteringEvent.id == event_id).first()
            if not event:
                return []
            
            alerts = []
            
            # Check for conditions that should trigger alerts
            duration = (datetime.utcnow() - event.start_time).total_seconds() / 60 if event.start_time else 0
            
            # High missing rate alert
            headcount_query = self.db.query(
                func.count(MusteringLog.id).label('total'),
                func.sum(func.case([(MusteringLog.status == 0, 1)], [(MusteringLog.status == 0, 1)]).label('missing')
            ).filter(MusteringLog.event_id == event_id)
            )
            
            headcount_result = headcount_query.first()
            missing_rate = (headcount_result.total / event.total_expected) if event.total_expected > 0 else 0
            
            if missing_rate > 0.3:  # More than 30% missing
                alerts.append({
                    'type': 'high_missing_rate',
                    'message': f'{round(missing_rate * 100, 1)}% of personnel missing',
                    'severity': 'high',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Long duration alert
            if duration > 20:  # More than 20 minutes
                alerts.append({
                    'type': 'long_duration',
                    'message': f'Event duration: {round(duration, 1)} minutes exceeds threshold',
                    'severity': 'medium',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # High-risk event type alert
            high_risk_types = [2, 3, 4]  # Fire, Gas, Man Down
            if event.event_type in high_risk_types:
                alerts.append({
                    'type': 'high_risk_event',
                    'message': f'High-risk event type: {event.event_type}',
                    'severity': 'critical',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
