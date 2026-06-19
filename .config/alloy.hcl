// 1. Discover the containers
discovery.docker "containers" {
  host = "unix:///var/run/docker.sock"
}

// 2. REWRITE the targets (this is where we create container_name)
discovery.relabel "add_container_label" {
  targets = discovery.docker.containers.targets

  rule {
    source_labels = ["__meta_docker_container_name"]
    // This regex looks for a slash followed by the name
    regex         = "/(.*)" 
    // This captures only the part after the slash
    replacement   = "$1"    
    target_label  = "container_name"
  }
}

// 3. Collect logs using the NEW targets
loki.source.docker "django_logs" {
  host    = "unix:///var/run/docker.sock"
  // Note: we use .output from discovery.relabel
  targets = discovery.relabel.add_container_label.output
  forward_to = [loki.process.django_process.receiver]
}

// 4. Process the log content (JSON parsing)
loki.process "django_process" {
  forward_to = [loki.write.loki.receiver]

  stage.json {
    expressions = {
      level  = "level",
      msg    = "msg",
      logger = "logger",
    }
  }

  stage.labels {
    values = {
      level  = "level",
      logger = "logger",
    }
  }
}

// 5. Send to Loki
loki.write "loki" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
  }
}