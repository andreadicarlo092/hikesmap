"""
CLI per la validazione manuale dei trailhead draft.
Uso:
  python validate_cli.py list          # mostra i draft
  python validate_cli.py approve <id>  # approva un trailhead
  python validate_cli.py approve-all   # approva tutti i draft
  python validate_cli.py reject <id>   # elimina un draft
  python validate_cli.py stats         # statistiche database
"""
import click
import psycopg2.extras
from db import get_connection


@click.group()
def cli():
    """CLI di validazione trailhead per Trail Explorer."""
    pass


@cli.command()
@click.option('--limit', default=50, help='Numero massimo di draft da mostrare')
def list(limit):
    """Mostra i trailhead draft in attesa di validazione."""
    conn = get_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT
                th.id,
                th.name,
                th.trail_count,
                th.source,
                ST_Y(th.geom) AS lat,
                ST_X(th.geom) AS lon
            FROM trailheads th
            WHERE th.validated = FALSE
            ORDER BY th.trail_count DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
    conn.close()

    if not rows:
        click.echo('Nessun trailhead in attesa di validazione.')
        return

    click.echo(f'Trailhead draft ({len(rows)} mostrati):')
    click.echo(f'{"ID":>6}  {"Nome":<40}  {"Sentieri":>8}  {"Lat":>10}  {"Lon":>10}')
    click.echo('-' * 80)
    for r in rows:
        nome = r['name'] or '(senza nome)'
        click.echo(f'{r["id"]:>6}  {nome[:40]:<40}  {r["trail_count"]:>8}  {r["lat"]:>10.5f}  {r["lon"]:>10.5f}')


@cli.command()
@click.argument('trailhead_id', type=int)
def approve(trailhead_id):
    """Approva un trailhead draft (lo rende visibile via API)."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE trailheads SET validated = TRUE WHERE id = %s AND validated = FALSE RETURNING id",
            (trailhead_id,)
        )
        updated = cur.fetchone()
    conn.commit()
    conn.close()
    if updated:
        click.echo(f'Trailhead {trailhead_id} approvato.')
    else:
        click.echo(f'Trailhead {trailhead_id} non trovato o gia validato.')


@cli.command('approve-all')
def approve_all():
    """Approva tutti i trailhead draft."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE trailheads SET validated = TRUE WHERE validated = FALSE RETURNING id")
        ids = [r[0] for r in cur.fetchall()]
    conn.commit()
    conn.close()
    click.echo(f'Approvati {len(ids)} trailhead.')


@cli.command()
@click.argument('trailhead_id', type=int)
def reject(trailhead_id):
    """Elimina un trailhead draft."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM trailheads WHERE id = %s AND validated = FALSE RETURNING id",
            (trailhead_id,)
        )
        deleted = cur.fetchone()
    conn.commit()
    conn.close()
    if deleted:
        click.echo(f'Trailhead {trailhead_id} eliminato.')
    else:
        click.echo(f'Trailhead {trailhead_id} non trovato o gia validato (non eliminabile).')


@cli.command()
def stats():
    """Mostra statistiche del database."""
    conn = get_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT COUNT(*) AS n FROM trails")
        n_trails = cur.fetchone()['n']
        cur.execute("SELECT COUNT(*) AS n FROM trailheads WHERE validated = TRUE")
        n_validated = cur.fetchone()['n']
        cur.execute("SELECT COUNT(*) AS n FROM trailheads WHERE validated = FALSE")
        n_draft = cur.fetchone()['n']
        cur.execute("SELECT COUNT(*) AS n FROM trails WHERE elevation_profile IS NOT NULL")
        n_elev = cur.fetchone()['n']
        cur.execute("""
            SELECT status, COUNT(*) AS n, MAX(completed_at) AS last_run
            FROM etl_run_log
            GROUP BY status
            ORDER BY status
        """)
        runs = cur.fetchall()
    conn.close()

    click.echo('=== Trail Explorer -- Statistiche DB ===')
    click.echo(f'Sentieri importati:          {n_trails}')
    click.echo(f'Trailhead validati:          {n_validated}')
    click.echo(f'Trailhead draft:             {n_draft}')
    click.echo(f'Sentieri con profilo altim.: {n_elev}')
    click.echo('---')
    if runs:
        click.echo('ETL run log:')
        for r in runs:
            last = r['last_run'].strftime('%Y-%m-%d %H:%M') if r['last_run'] else 'mai'
            click.echo(f'  {r["status"]}: {r["n"]} run, ultimo {last}')


if __name__ == '__main__':
    cli()
