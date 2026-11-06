import type { Decision, DecisionOption } from "../types";
import { BoardIcon, svgButton } from "./boardLayout";

const PANEL_X = 6;
const PANEL_Y = 336;
const PANEL_WIDTH = 130;
const TITLE_HEIGHT = 22;
const ROW_HEIGHT = 29;

// As printed on the board, in its order: the project, what it costs without a discount, its icon, and
// in words what it does.
const PROJECTS = [
  { project: "sell_patents", name: "Sell Patents", price: "X", icon: "resources/card", iconWidth: 13, does: "Discard any number of cards for 1 MegaCredit each" },
  { project: "power_plant", name: "Power Plant", price: "11", icon: "resources/power", does: "Raise your energy Production 1 step" },
  { project: "asteroid", name: "Asteroid", price: "14", icon: "global-parameters/temperature", iconWidth: 6, does: "Raise Temperature 1 step" },
  { project: "aquifer", name: "Aquifer", price: "18", icon: "tiles/ocean", does: "Place an Ocean" },
  { project: "greenery", name: "Greenery", price: "23", icon: "tiles/greenery", does: "Place a Greenery" },
  { project: "city", name: "City", price: "25", icon: "tiles/city", does: "Place a City and raise your MegaCredit Production 1 step" },
];

interface Props {
  decision: Decision | null;
  /** True while a pick is on its way to the server. */
  disabled: boolean;
  onPick: (sequence: number, index: number) => void;
}

/** The Standard Projects panel at the lower left of the board. Those the Decision offers are lit and
 * clicked here, at their price after any discount; while it offers some, the rest step back. */
export function StandardProjects({ decision, disabled, onPick }: Props) {
  const offered = new Map<string, DecisionOption>();
  for (const option of decision?.options ?? []) {
    if (option.details.type === "standard_project") offered.set(option.details.project as string, option);
  }
  return (
    <g className="standard-projects" transform={`translate(${PANEL_X} ${PANEL_Y})`} role="group" aria-label="Standard Projects">
      <rect className="standard-projects-panel" width={PANEL_WIDTH} height={TITLE_HEIGHT + ROW_HEIGHT * PROJECTS.length + 4} rx={9} />
      <text className="standard-projects-title" x={PANEL_WIDTH / 2} y={TITLE_HEIGHT / 2 + 1}>
        Standard Projects
      </text>
      {PROJECTS.map(({ project, name, price, icon, iconWidth, does }, row) => {
        const option = offered.get(project);
        const state = option ? "offered" : offered.size > 0 ? "not-offered" : "";
        const cost = option && project !== "sell_patents" ? String(option.details.cost) : price;
        const press = () => {
          if (decision && option && !disabled) onPick(decision.sequence, option.index);
        };
        return (
          <g
            key={project}
            className={`standard-project ${state}`}
            transform={`translate(4 ${TITLE_HEIGHT + row * ROW_HEIGHT})`}
            {...(option ? svgButton(option.label, press) : {})}
          >
            <title>{`${name}: ${does}`}</title>
            <rect className="standard-project-row" width={PANEL_WIDTH - 8} height={ROW_HEIGHT - 3} rx={5} />
            <rect className="price-token" x={3} y={3} width={21} height={20} rx={4} />
            <text className="price-token-text" x={13.5} y={13}>
              {cost}
            </text>
            <BoardIcon path={icon} x={35} y={13} size={iconWidth ?? 18} height={18} />
            <text className="standard-project-name" x={46} y={13}>
              {name}
            </text>
          </g>
        );
      })}
    </g>
  );
}
