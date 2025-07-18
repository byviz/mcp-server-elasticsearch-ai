"""
Herramientas optimizadas para Elasticsearch MCP basadas en análisis de datos APM reales.

Implementa herramientas especializadas para:
1. Análisis de performance de traces con waterfall
2. Detección de patrones de errores para RCA
3. Correlación de eventos de negocio con APM
4. Análisis de rendimiento por servicio
5. Detección de anomalías

"""

from datetime import datetime, timedelta

import httpx


class OptimizedAPMTools:
    """Herramientas optimizadas para análisis APM basadas en datos reales."""

    def __init__(self, elasticsearch_client):
        """Initialize with Elasticsearch client."""
        self.client = elasticsearch_client

    async def _search(self, index: str, query: dict) -> dict:
        """Execute search with error handling."""
        try:
            # Usar el cliente de Elasticsearch existente
            if hasattr(self.client, 'search'):
                return await self.client.search(index, query)
            else:
                # Fallback para clientes HTTP directos
                url = f"{self.client.base_url}/{index}/_search"
                headers = self.client.get_auth_headers()

                async with httpx.AsyncClient(verify=False) as client:
                    response = await client.post(url, headers=headers, json=query)
                    response.raise_for_status()
                    return response.json()
        except Exception as e:
            print(f"Error en búsqueda {index}: {e}")
            return {}

    async def analyze_trace_performance(self, trace_id: str, include_errors: bool = True,
                                      include_metrics: bool = True) -> dict:
        """
        Análisis completo de performance de trace con waterfall y correlaciones.
        
        """

        result = {
            "trace_id": trace_id,
            "analysis": {
                "trace_info": {},
                "waterfall": [],
                "performance_metrics": {},
                "outliers": [],
                "correlations": {},
                "recommendations": []
            }
        }

        # 1. Obtener información básica del trace
        trace_query = {
            "size": 1,
            "query": {"term": {"trace.id": trace_id}},
            "_source": ["trace.id", "service.name", "transaction.name", "transaction.duration.us", "@timestamp"],
            "sort": [{"@timestamp": {"order": "desc"}}]
        }

        trace_result = await self._search("traces-apm*", trace_query)

        if not trace_result.get('hits', {}).get('hits'):
            result["error"] = "Trace not found"
            return result

        trace_hit = trace_result['hits']['hits'][0]['_source']
        result["analysis"]["trace_info"] = {
            "service": trace_hit.get("service", {}).get("name", "Unknown"),
            "transaction": trace_hit.get("transaction", {}).get("name", "Unknown"),
            "duration_ms": trace_hit.get("transaction", {}).get("duration", {}).get("us", 0) / 1000,
            "timestamp": trace_hit.get("@timestamp", "Unknown")
        }

        # 2. Obtener todos los spans del trace ordenados cronológicamente
        spans_query = {
            "size": 100,
            "query": {"term": {"trace.id": trace_id}},
            "sort": [{"@timestamp": {"order": "asc"}}],
            "_source": [
                "span.id", "span.name", "span.duration.us", "@timestamp",
                "service.name", "span.type", "span.subtype"
            ]
        }

        spans_result = await self._search("traces-apm*", spans_query)

        if spans_result.get('hits', {}).get('hits'):
            spans = spans_result['hits']['hits']
            total_duration = 0

            # Construir waterfall
            for span in spans:
                span_source = span['_source']
                duration_us = span_source.get('span', {}).get('duration', {}).get('us', 0)
                duration_ms = duration_us / 1000

                span_data = {
                    "span_id": span_source.get("span", {}).get("id", "N/A")[:8],
                    "name": span_source.get("span", {}).get("name", "N/A"),
                    "duration_ms": duration_ms,
                    "service": span_source.get("service", {}).get("name", "N/A"),
                    "type": span_source.get("span", {}).get("type", "N/A"),
                    "subtype": span_source.get("span", {}).get("subtype", "N/A"),
                    "timestamp": span_source.get("@timestamp", "N/A")
                }

                result["analysis"]["waterfall"].append(span_data)
                total_duration += duration_ms

            # Calcular métricas de performance
            durations = [span["duration_ms"] for span in result["analysis"]["waterfall"]]
            if durations:
                result["analysis"]["performance_metrics"] = {
                    "total_spans": len(spans),
                    "total_duration_ms": total_duration,
                    "avg_duration_ms": sum(durations) / len(durations),
                    "max_duration_ms": max(durations),
                    "min_duration_ms": min(durations)
                }

                # Detectar outliers (spans > 2x promedio)
                avg_duration = result["analysis"]["performance_metrics"]["avg_duration_ms"]
                result["analysis"]["outliers"] = [
                    span for span in result["analysis"]["waterfall"]
                    if span["duration_ms"] > avg_duration * 2
                ]

        # 3. Buscar errores correlacionados
        if include_errors:
            error_query = {
                "size": 10,
                "query": {"term": {"trace.id": trace_id}},
                "_source": ["error.exception", "service.name", "@timestamp"]
            }

            error_result = await self._search("logs-apm.error-*", error_query)
            errors_found = error_result.get('hits', {}).get('total', {}).get('value', 0)

            result["analysis"]["correlations"]["errors_found"] = errors_found

            if errors_found > 0:
                result["analysis"]["correlations"]["errors"] = []
                for error in error_result['hits']['hits']:
                    error_source = error['_source']
                    exceptions = error_source.get('error', {}).get('exception', [])

                    if exceptions:
                        error_data = {
                            "type": exceptions[0].get('type', 'Unknown'),
                            "message": exceptions[0].get('message', 'N/A')[:100],
                            "service": error_source.get('service', {}).get('name', 'Unknown'),
                            "timestamp": error_source.get('@timestamp', 'Unknown')
                        }
                        result["analysis"]["correlations"]["errors"].append(error_data)

        # 4. Buscar métricas correlacionadas
        if include_metrics:
            timestamp = result["analysis"]["trace_info"]["timestamp"]
            if timestamp != "Unknown":
                try:
                    time_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_start = (time_obj - timedelta(minutes=5)).isoformat()
                    time_end = (time_obj + timedelta(minutes=5)).isoformat()

                    metrics_query = {
                        "size": 5,
                        "query": {
                            "bool": {
                                "must": [
                                    {"term": {"service.name": result["analysis"]["trace_info"]["service"]}},
                                    {"range": {"@timestamp": {"gte": time_start, "lte": time_end}}}
                                ]
                            }
                        },
                        "_source": ["metricset.name", "@timestamp"]
                    }

                    metrics_result = await self._search("metrics-apm*", metrics_query)
                    metrics_found = metrics_result.get('hits', {}).get('total', {}).get('value', 0)
                    result["analysis"]["correlations"]["metrics_found"] = metrics_found
                except Exception as e:
                    result["analysis"]["correlations"]["metrics_error"] = str(e)

        # 5. Generar recomendaciones basadas en análisis
        recommendations = []

        # Recomendaciones por outliers
        for outlier in result["analysis"]["outliers"]:
            recommendations.append(
                f"Investigar span lento: {outlier['service']}.{outlier['name']} ({outlier['duration_ms']:.1f}ms)"
            )

        # Recomendaciones por duración total
        total_duration = result["analysis"]["performance_metrics"].get("total_duration_ms", 0)
        if total_duration > 1000:
            recommendations.append("Trace excede 1s - considerar optimizaciones")

        # Recomendaciones por número de spans
        total_spans = result["analysis"]["performance_metrics"].get("total_spans", 0)
        if total_spans > 20:
            recommendations.append("Trace con muchos spans - considerar reducir llamadas")

        # Recomendaciones por errores
        if result["analysis"]["correlations"].get("errors_found", 0) > 0:
            recommendations.append(
                f"Investigar {result['analysis']['correlations']['errors_found']} errores relacionados"
            )

        result["analysis"]["recommendations"] = recommendations

        return result

    async def find_error_patterns(self, time_range: str = "now-24h",
                                 service_name: str | None = None,
                                 error_type: str | None = None,
                                 min_frequency: int = 1) -> dict:
        """
        Análisis de patrones de errores para RCA automatizado.
        
        """

        result = {
            "analysis": {
                "time_range": time_range,
                "filters": {
                    "service_name": service_name,
                    "error_type": error_type,
                    "min_frequency": min_frequency
                },
                "error_patterns": [],
                "timeline": [],
                "affected_services": [],
                "recommendations": []
            }
        }

        # Construir query base
        query_filters = [{"range": {"@timestamp": {"gte": time_range}}}]
        if service_name:
            query_filters.append({"term": {"service.name": service_name}})
        if error_type:
            query_filters.append({"term": {"error.exception.type": error_type}})

        # Agregación de patrones de errores
        error_patterns_query = {
            "size": 0,
            "query": {"bool": {"must": query_filters}},
            "aggs": {
                "error_types": {
                    "terms": {
                        "field": "error.exception.type",
                        "size": 10,
                        "min_doc_count": min_frequency
                    },
                    "aggs": {
                        "services": {
                            "terms": {"field": "service.name", "size": 5}
                        },
                        "transactions": {
                            "terms": {"field": "transaction.name", "size": 5}
                        },
                        "timeline": {
                            "date_histogram": {
                                "field": "@timestamp",
                                "fixed_interval": "1h"
                            }
                        },
                        "recent_errors": {
                            "top_hits": {
                                "size": 3,
                                "_source": [
                                    "error.exception.message", "service.name",
                                    "@timestamp", "trace.id", "transaction.name"
                                ],
                                "sort": [{"@timestamp": {"order": "desc"}}]
                            }
                        }
                    }
                }
            }
        }

        patterns_result = await self._search("logs-apm.error-*", error_patterns_query)

        if patterns_result.get('aggregations', {}).get('error_types', {}).get('buckets'):
            error_buckets = patterns_result['aggregations']['error_types']['buckets']

            for bucket in error_buckets:
                error_type_name = bucket['key'] if bucket['key'] else 'Unknown'
                frequency = bucket['doc_count']

                # Servicios afectados
                services = [s['key'] for s in bucket.get('services', {}).get('buckets', [])]

                # Transacciones afectadas
                transactions = [t['key'] for t in bucket.get('transactions', {}).get('buckets', [])]

                # Timeline para detectar spikes
                timeline_buckets = bucket.get('timeline', {}).get('buckets', [])
                timeline = []
                for time_bucket in timeline_buckets:
                    if time_bucket['doc_count'] > 0:
                        timeline.append({
                            "timestamp": time_bucket['key_as_string'],
                            "count": time_bucket['doc_count']
                        })

                # Análisis de tendencia
                trend = "stable"
                if len(timeline) >= 2:
                    recent_count = sum(t['count'] for t in timeline[-2:])
                    older_count = sum(t['count'] for t in timeline[:-2])

                    if recent_count > older_count * 1.5:
                        trend = "increasing"
                    elif recent_count < older_count * 0.5:
                        trend = "decreasing"

                # Ejemplos recientes
                examples = []
                if bucket.get('recent_errors', {}).get('hits', {}).get('hits'):
                    for hit in bucket['recent_errors']['hits']['hits']:
                        source = hit['_source']
                        exceptions = source.get('error', {}).get('exception', [])
                        message = exceptions[0].get('message', 'N/A') if exceptions else 'N/A'

                        examples.append({
                            "message": message[:100] + "..." if len(message) > 100 else message,
                            "service": source.get('service', {}).get('name', 'N/A'),
                            "trace_id": source.get('trace', {}).get('id', 'N/A'),
                            "transaction": source.get('transaction', {}).get('name', 'N/A'),
                            "timestamp": source.get('@timestamp', 'N/A')
                        })

                pattern_data = {
                    "error_type": error_type_name,
                    "frequency": frequency,
                    "affected_services": services,
                    "affected_transactions": transactions,
                    "trend": trend,
                    "timeline": timeline,
                    "recent_examples": examples
                }

                result["analysis"]["error_patterns"].append(pattern_data)

        # Generar recomendaciones basadas en patrones
        recommendations = []

        for pattern in result["analysis"]["error_patterns"]:
            # Recomendaciones por frecuencia
            if pattern['frequency'] > min_frequency * 5:
                recommendations.append(
                    f"Alta frecuencia de {pattern['error_type']}: {pattern['frequency']} ocurrencias - prioridad crítica"
                )
            elif pattern['frequency'] > min_frequency * 2:
                recommendations.append(
                    f"Frecuencia elevada de {pattern['error_type']}: {pattern['frequency']} ocurrencias - prioridad alta"
                )

            # Recomendaciones por servicios afectados
            if len(pattern['affected_services']) > 3:
                recommendations.append(
                    f"Error {pattern['error_type']} afecta múltiples servicios - posible problema sistémico"
                )

            # Recomendaciones por tendencia
            if pattern['trend'] == "increasing":
                recommendations.append(
                    f"Tendencia creciente en {pattern['error_type']} - investigar causa raíz urgente"
                )

            # Recomendaciones específicas para ConnectionError (basado en datos reales)
            if pattern['error_type'] == 'ConnectionError':
                if any('localhost' in ex['message'] for ex in pattern['recent_examples']):
                    recommendations.append(
                        "ConnectionError a localhost detectado - verificar servicios locales y puertos"
                    )

            # Detectar spikes temporales
            if pattern['timeline']:
                max_count = max(t['count'] for t in pattern['timeline'])
                avg_count = sum(t['count'] for t in pattern['timeline']) / len(pattern['timeline'])

                if max_count > avg_count * 3:
                    recommendations.append(
                        f"Spike temporal detectado en {pattern['error_type']} - investigar evento específico"
                    )

        result["analysis"]["recommendations"] = recommendations

        return result

    async def correlate_business_events(self, correlation_id: str,
                                      time_window: str = "30m",
                                      include_user_journey: bool = False) -> dict:
        """
        Correlación de eventos de negocio con datos APM.
        
        Busca el correlation_id en múltiples índices para reconstruir
        el journey completo de un evento de negocio.
        
        """

        result = {
            "correlation_id": correlation_id,
            "analysis": {
                "apm_events": [],
                "business_logs": [],
                "timeline": [],
                "correlations_found": 0,
                "issues_detected": []
            }
        }

        # Campos comunes de correlación a buscar
        correlation_fields = [
            "trace.id", "span.id", "transaction.id",
            "user.id", "correlation_id", "request_id", "session_id"
        ]

        # 1. Buscar en traces APM
        apm_events = []
        for field in correlation_fields:
            apm_query = {
                "size": 50,
                "query": {"term": {field: correlation_id}},
                "_source": [
                    "trace.id", "span.id", "service.name", "transaction.name",
                    "span.name", "span.duration.us", "@timestamp", field
                ],
                "sort": [{"@timestamp": {"order": "asc"}}]
            }

            apm_result = await self._search("traces-apm*", apm_query)

            if apm_result.get('hits', {}).get('hits'):
                for hit in apm_result['hits']['hits']:
                    event_data = {
                        "source": "APM",
                        "field_matched": field,
                        "trace_id": hit['_source'].get('trace', {}).get('id', 'N/A'),
                        "span_id": hit['_source'].get('span', {}).get('id', 'N/A'),
                        "service": hit['_source'].get('service', {}).get('name', 'N/A'),
                        "transaction": hit['_source'].get('transaction', {}).get('name', 'N/A'),
                        "span_name": hit['_source'].get('span', {}).get('name', 'N/A'),
                        "duration_ms": hit['_source'].get('span', {}).get('duration', {}).get('us', 0) / 1000,
                        "timestamp": hit['_source'].get('@timestamp', 'N/A')
                    }
                    apm_events.append(event_data)
                break  # Solo usar el primer campo que tenga resultados

        result["analysis"]["apm_events"] = apm_events

        # 2. Buscar en logs de negocio
        business_logs = []

        # Buscar en múltiples patrones de logs
        log_patterns = ["filebeat-*", "logs-*"]

        for pattern in log_patterns:
            business_query = {
                "size": 50,
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"message": correlation_id}},
                            {"term": {"correlation_id": correlation_id}},
                            {"term": {"request_id": correlation_id}},
                            {"term": {"transaction_id": correlation_id}},
                            {"term": {"trace.id": correlation_id}}
                        ]
                    }
                },
                "_source": ["message", "host.name", "service.name", "@timestamp", "log.level"],
                "sort": [{"@timestamp": {"order": "asc"}}]
            }

            business_result = await self._search(pattern, business_query)

            if business_result.get('hits', {}).get('hits'):
                for hit in business_result['hits']['hits']:
                    log_data = {
                        "source": "Business Log",
                        "index_pattern": pattern,
                        "message": str(hit['_source'].get('message', 'N/A'))[:200],
                        "host": hit['_source'].get('host', {}).get('name', 'N/A'),
                        "service": hit['_source'].get('service', {}).get('name', 'N/A'),
                        "level": hit['_source'].get('log', {}).get('level', 'N/A'),
                        "timestamp": hit['_source'].get('@timestamp', 'N/A')
                    }
                    business_logs.append(log_data)

        result["analysis"]["business_logs"] = business_logs

        # 3. Crear timeline combinado
        all_events = []

        # Añadir eventos APM
        for event in apm_events:
            all_events.append({
                "timestamp": event["timestamp"],
                "type": "APM",
                "description": f"{event['service']}.{event['transaction']} ({event['duration_ms']:.1f}ms)",
                "data": event
            })

        # Añadir logs de negocio
        for log in business_logs:
            all_events.append({
                "timestamp": log["timestamp"],
                "type": "Log",
                "description": f"{log['host']}: {log['message'][:50]}...",
                "data": log
            })

        # Ordenar por timestamp
        all_events.sort(key=lambda x: x["timestamp"] if x["timestamp"] != "N/A" else "")
        result["analysis"]["timeline"] = all_events

        # 4. Análisis de correlaciones y detección de issues
        result["analysis"]["correlations_found"] = len(apm_events) + len(business_logs)

        issues = []

        if apm_events and business_logs:
            issues.append("Correlación exitosa entre APM y logs de negocio")
        elif apm_events and not business_logs:
            issues.append("Solo datos APM encontrados - verificar logs de negocio")
        elif business_logs and not apm_events:
            issues.append("Solo logs de negocio encontrados - verificar instrumentación APM")
        else:
            issues.append("No se encontraron correlaciones - verificar correlation_id")

        # Detectar gaps temporales grandes
        if len(all_events) > 1:
            timestamps = []
            for event in all_events:
                if event["timestamp"] != "N/A":
                    try:
                        timestamps.append(datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00')))
                    except:
                        continue

            if len(timestamps) > 1:
                time_span = (max(timestamps) - min(timestamps)).total_seconds()
                if time_span > 300:  # > 5 minutos
                    issues.append(
                        f"Journey largo detectado: {time_span/60:.1f} minutos - posible problema de performance"
                    )
                elif time_span < 1:  # < 1 segundo
                    issues.append(
                        f"Journey muy rápido: {time_span:.2f} segundos - operación eficiente"
                    )

        result["analysis"]["issues_detected"] = issues

        return result
